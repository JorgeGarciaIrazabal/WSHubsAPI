import os
import shutil
import unittest
from os import listdir
from wshubsapi.client_file_generator.java_file_generator import JAVAFileGenerator
from wshubsapi.client_file_generator.js_file_generator import JSClientFileGenerator
from wshubsapi.client_file_generator.python_file_generator import PythonClientFileGenerator
from wshubsapi.hub import Hub
from wshubsapi.hub import HubError
from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.hubs_inspector import HubsInspectorError
from wshubsapi.Test.utils.HubsUtils import removeHubsSubclasses

# do not remove this
from wshubsapi.utils__api_hub import UtilsAPIHub

class TestHubDetection(unittest.TestCase):
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
        removeHubsSubclasses()

    def test_hubsInspection(self):
        self.assertEqual(len(HubsInspector.HUBS_DICT), 3, 'Detects all Hubs')
        self.assertTrue(issubclass(HubsInspector.HUBS_DICT['TestHub'].__class__, Hub), 'Hubs subclass is class')
        self.assertTrue(issubclass(HubsInspector.HUBS_DICT['TestHub2'].__class__, Hub), 'Hubs subclass is class')
        self.assertTrue(getattr(HubsInspector.HUBS_DICT['TestHub'], "getData"), 'Detects function')

    def test_hubsLimitations(self):
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

    def test_hubsLimitations_startWithUnderscores(self):
        class __TestHubLimitation(Hub):
            pass

        self.assertRaises(HubError, HubsInspector.inspect_implemented_hubs, force_reconstruction=True)

    def test_hubsLimitations_cant_be_named_wsClient(self):
        class wsClient(Hub):
            pass

        self.assertRaises(HubError, HubsInspector.inspect_implemented_hubs, force_reconstruction=True)

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

    def tearDown(self):
        removeHubsSubclasses()

        try:
            otherPath = "onTest"
            os.removedirs(otherPath)
        except:
            pass
        try:
            fullPath = os.path.join(otherPath, JSClientFileGenerator.FILE_NAME)
            os.remove(fullPath)
        except:
            pass
        try:
            fullPath = os.path.join(otherPath, PythonClientFileGenerator.FILE_NAME)
            packageFilePath = os.path.join(otherPath, "__init__.py")
            os.remove(fullPath)
            os.remove(packageFilePath)
            os.removedirs("onTest")
        except:
            pass

    def test_JSCreation(self):
        HubsInspector.construct_js_file()

        self.assertTrue(os.path.exists(JSClientFileGenerator.FILE_NAME))
        os.remove(JSClientFileGenerator.FILE_NAME)

        otherPath = "onTest"
        fullPath = os.path.join(otherPath, JSClientFileGenerator.FILE_NAME)
        HubsInspector.construct_js_file(otherPath)

        self.assertTrue(os.path.exists(fullPath))

    def test_JAVACreation(self):
        path = "onTest"
        try:
            HubsInspector.construct_java_file("test", path)
            self.assertTrue(os.path.exists(os.path.join(path, JAVAFileGenerator.SERVER_FILE_NAME)))
            self.assertTrue(os.path.exists(os.path.join(path, JAVAFileGenerator.CLIENT_PACKAGE_NAME)))
        finally:
            for f in listdir(path):
                fullPath = os.path.join(path, f)
                os.remove(fullPath) if os.path.isfile(fullPath) else shutil.rmtree(fullPath)

    def test_PythonCreation(self):
        HubsInspector.construct_python_file()
        self.assertTrue(os.path.exists(PythonClientFileGenerator.FILE_NAME))
        self.assertTrue(os.path.exists("__init__.py"), "Check if python package is created")
        os.remove(PythonClientFileGenerator.FILE_NAME)

        otherPath = "onTest"
        fullPath = os.path.join(otherPath, PythonClientFileGenerator.FILE_NAME)
        packageFilePath = os.path.join(otherPath, "__init__.py")
        HubsInspector.construct_python_file(otherPath)
        self.assertTrue(os.path.exists(fullPath))
        self.assertTrue(os.path.exists(packageFilePath), "Check if python package is created")
