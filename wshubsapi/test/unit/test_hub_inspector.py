import os
import shutil
import unittest
from os import listdir

from wshubsapi.client_file_generator.client_file_generator import ClientFileGenerator
from wshubsapi.client_file_generator.java_file_generator import JAVAFileGenerator
from wshubsapi.client_file_generator.js_file_generator import JSClientFileGenerator
from wshubsapi.client_file_generator.python_file_generator import PythonClientFileGenerator
from wshubsapi.hub import Hub
from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.hubs_inspector import HubsInspectorError, HubError
from wshubsapi.test.utils.hubs_utils import remove_hubs_subclasses

# do not remove this
from wshubsapi.utils_api_hub import UtilsAPIHub


class TestHubInspector(unittest.TestCase):
    def setUp(self):
        # Building hubs for testing
        class TestHub(Hub):
            def getData(self):
                pass

        class TestHub2(Hub):
            pass

        self.testHubClass = TestHub
        self.testHub2Class = TestHub2
        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)

    def tearDown(self):
        del self.testHubClass
        del self.testHub2Class
        remove_hubs_subclasses()

    def test_constructor_should_raise_exception(self):
        def create_instance():
            return HubsInspector()

        self.assertRaises(HubsInspectorError, create_instance)

    def test_hubs_inspection(self):
        self.assertEqual(len(HubsInspector.HUBS_DICT), 3, 'Detects all Hubs')
        self.assertTrue(issubclass(HubsInspector.HUBS_DICT['TestHub'].__class__, Hub), 'Hubs subclass is class')
        self.assertTrue(issubclass(HubsInspector.HUBS_DICT['TestHub2'].__class__, Hub), 'Hubs subclass is class')
        self.assertTrue(getattr(HubsInspector.HUBS_DICT['TestHub'], "getData"), 'Detects function')

    def test_hubs_limitations(self):
        class TestHubLimitation(Hub):
            pass

        class TestHubLimitation2(Hub):
            __HubName__ = "TestHubLimitation"

        self.assertRaises(HubError, HubsInspector.inspect_implemented_hubs, force_reconstruction=True)
        TestHubLimitation2.__HubName__ = "TestHubLimitation2"

        class TestHubLimitation3(Hub):
            def __init__(self, aux):
                super(TestHubLimitation3, self).__init__()

        self.assertRaises(HubsInspectorError, HubsInspector.inspect_implemented_hubs, force_reconstruction=True)
        TestHubLimitation3.__init__ = lambda: 1 + 1

    def test_hubs_limitations_starts_with_underscores(self):
        class __TestHubLimitation(Hub):
            pass

        self.assertRaises(HubError, HubsInspector.inspect_implemented_hubs, force_reconstruction=True)

    def test_hubs_limitations_cant_be_named_ws_client(self):
        class ws_client(Hub):
            pass

        self.assertRaises(HubError, HubsInspector.inspect_implemented_hubs, force_reconstruction=True)

    def test_HubCreation_insertsInstanceInHUBs_DICT(self):
        class TestHub1(Hub):
            pass

        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)

        self.assertTrue(HubsInspector.get_hub_instance(TestHub1) in HubsInspector.HUBS_DICT.values())

    def test_hub_creation_inserts_new__HubName__in_HUBS_DICT(self):
        class TestHub1(Hub):
            __HubName__ = "newValue"
            pass

        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)

        self.assertIn("newValue", HubsInspector.HUBS_DICT.keys())

    def test_HubCreation_RaisesExceptionIfClassNameStartsWith__(self):
        class __TestHub1(Hub):
            pass

        self.assertRaises(HubError, HubsInspector.inspect_implemented_hubs, True)

    def test_HubCreation_RaisesExceptionIfClassNameIsWsClient(self):
        class ws_client(Hub):
            pass

        self.assertRaises(HubError, HubsInspector.inspect_implemented_hubs, True)

    def test_getHubInstance_returnsAnInstanceOfHubIfExists(self):
        self.assertIsInstance(HubsInspector.get_hub_instance(self.testHubClass), Hub)

    def test_getHubInstance_RaisesErrorIfNotAHub(self):
        self.assertRaises(AttributeError, HubsInspector.get_hub_instance, (str,))

    def test_getHubsInformation_ReturnsDictionaryWithNoClientFunctions(self):
        infoReport = HubsInspector.get_hubs_information()

        self.assertIn("TestHub2", infoReport)
        self.assertIn("getData", infoReport["TestHub"]["serverMethods"])

    def test_getHubsInformation_ReturnsDictionaryWithClientFunctions(self):
        class TestHubWithClient(Hub):
            def getData(self):
                pass

            def _define_client_functions(self):
                self.client_functions = dict(client1=lambda x, y: None,
                                             client2=lambda x, y=1: None,
                                             client3=lambda x=0, y=1: None)

        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)

        infoReport = HubsInspector.get_hubs_information()

        self.assertIn("TestHubWithClient", infoReport)
        client1Method = infoReport["TestHubWithClient"]["clientMethods"]["client1"]
        client2Method = infoReport["TestHubWithClient"]["clientMethods"]["client2"]
        client3Method = infoReport["TestHubWithClient"]["clientMethods"]["client3"]
        self.assertEqual(client1Method["args"], ["x", "y"])
        self.assertEqual(client2Method["defaults"], [1])
        self.assertEqual(client3Method["defaults"], [0, 1])


class TestClientFileConstructor(unittest.TestCase):
    def setUp(self):
        class TestHub(Hub):
            def getData(self):
                pass

        class TestHub2(Hub):
            def getData(self):
                pass

        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)
        self.other_folder = "onTest"
        self.other_name = "on_test"
        self.temp_folder = "__temp_file__"
        self.original_working_directory = os.getcwd()
        if os.path.exists(self.temp_folder):
            shutil.rmtree(self.temp_folder)
        os.makedirs(self.temp_folder)
        os.chdir(self.temp_folder)

    def tearDown(self):
        remove_hubs_subclasses()
        os.chdir(self.original_working_directory)
        shutil.rmtree(self.temp_folder)

    def test_construct_api_path_makeFoldersEvenIfNotExits(self):
        new_folder = os.path.join("test", "new", "folder", "api.py")
        self.assertFalse(os.path.exists(os.path.dirname(new_folder)))
        ClientFileGenerator._construct_api_path(new_folder)

        self.assertTrue(os.path.exists(os.path.dirname(new_folder)))

    def test_construct_api_path_returnParentPath(self):
        new_folder = os.path.join("test", "new", "folder", "api.py")
        parent_path = ClientFileGenerator._construct_api_path(new_folder)

        self.assertEqual(parent_path, os.path.abspath(os.path.dirname(new_folder)))

    def test_JSCreation_default_path(self):
        HubsInspector.construct_js_file()

        self.assertTrue(os.path.exists(HubsInspector.DEFAULT_JS_API_FILE_NAME))

    def test_JSCreation_new_path(self):
        full_path = os.path.join(self.other_folder, self.other_name)
        HubsInspector.construct_js_file(full_path)

        self.assertTrue(os.path.exists(full_path))

    @unittest.skip("no Java client ready")
    def test_JAVACreation(self):
        path = "onTest"
        try:
            HubsInspector.construct_java_file("test", path)
            self.assertTrue(os.path.exists(os.path.join(path, JAVAFileGenerator.SERVER_FILE_NAME)))
            self.assertTrue(os.path.exists(os.path.join(path, JAVAFileGenerator.CLIENT_PACKAGE_NAME)))
        finally:
            for f in listdir(path):
                full_path = os.path.join(path, f)
                os.remove(full_path) if os.path.isfile(full_path) else shutil.rmtree(full_path)

    def test_PythonCreation_default_values(self):
        HubsInspector.construct_python_file()
        self.assertTrue(os.path.exists(HubsInspector.DEFAULT_PY_API_FILE_NAME))
        self.assertTrue(os.path.exists("__init__.py"), "Check if python package is created")
        os.remove(HubsInspector.DEFAULT_PY_API_FILE_NAME)

    def test_PythonCreation_new_path(self):
        full_path = os.path.join(self.other_folder, self.other_name)
        package_file_path = os.path.join(self.other_folder, "__init__.py")
        HubsInspector.construct_python_file(full_path)
        self.assertTrue(os.path.exists(full_path))
        self.assertTrue(os.path.exists(package_file_path), "Check if python package is created")
