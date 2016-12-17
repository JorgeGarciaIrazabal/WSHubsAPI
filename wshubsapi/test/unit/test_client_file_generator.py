import os
import shutil
import unittest

from wshubsapi.client_file_generator.client_file_generator import ClientFileGenerator
from wshubsapi.client_file_generator.java_file_generator import JAVAFileGenerator
from wshubsapi.hub import Hub
from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.test.utils.hubs_utils import remove_hubs_subclasses


class TestClientFileGenerator(unittest.TestCase):
    def setUp(self):
        class TestHub(Hub):
            def get_data(self):
                pass

        class TestHub2(Hub):
            def get_data(self):
                pass

        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)
        self.other_folder = "onTest"
        self.other_name = "on_test"
        self.temp_folder = "__temp_folder__"
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

    def test_JSCreation_withClientFunctions(self):
        class TestHubWithClient(Hub):
            def get_data(self):
                pass

            def _define_client_functions(self):
                return dict(client1=lambda x, y: None,
                            client2=lambda x, y=1: None,
                            client3=lambda x=0, y=1: None)

        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)
        HubsInspector.construct_js_file()

        self.assertTrue(os.path.exists(HubsInspector.DEFAULT_JS_API_FILE_NAME))

    @unittest.skip("no Java client ready")
    def test_JAVACreation(self):
        path = "onTest"
        try:
            HubsInspector.construct_java_file("test", path)
            self.assertTrue(os.path.exists(os.path.join(path, JAVAFileGenerator.SERVER_FILE_NAME)))
            self.assertTrue(os.path.exists(os.path.join(path, JAVAFileGenerator.CLIENT_PACKAGE_NAME)))
        finally:
            for f in os.listdir(path):
                full_path = os.path.join(path, f)
                os.remove(full_path) if os.path.isfile(full_path) else shutil.rmtree(full_path)

    def test_PythonCreation_default_values(self):
        HubsInspector.construct_python_file()

        self.assertTrue(os.path.exists(HubsInspector.DEFAULT_PY_API_FILE_NAME))
        self.assertTrue(os.path.exists("__init__.py"), "Check if python package is created")

    def test_PythonCreation_withClientFunctions(self):
        class TestHubWithClient(Hub):
            def get_data(self):
                pass

            def _define_client_functions(self):
                return dict(client1=lambda x, y: None,
                            client2=lambda x, y=1: None,
                            client3=lambda x=0, y=1: None)

        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)
        HubsInspector.construct_python_file()

        self.assertTrue(os.path.exists(HubsInspector.DEFAULT_PY_API_FILE_NAME))

    def test_PythonCreation_new_path(self):
        full_path = os.path.join(self.other_folder, self.other_name)
        package_file_path = os.path.join(self.other_folder, "__init__.py")
        HubsInspector.construct_python_file(full_path)
        self.assertTrue(os.path.exists(full_path))
        self.assertTrue(os.path.exists(package_file_path), "Check if python package is created")

    def test_DartCreation_default_values(self):
        HubsInspector.construct_dart_file()

        self.assertTrue(os.path.exists(HubsInspector.DEFAULT_DART_API_FILE_NAME))

    def test_DartCreation_withClientFunctions(self):
        class TestHubWithClient(Hub):
            def get_data(self):
                pass

            def _define_client_functions(self):
                return dict(client1=lambda x, y: None,
                            client2=lambda x, y=1: None,
                            client3=lambda x=0, y=1: None)

        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)
        HubsInspector.construct_dart_file()

        self.assertTrue(os.path.exists(HubsInspector.DEFAULT_DART_API_FILE_NAME))

    def test_DartCreation_new_path(self):
        full_path = os.path.join(self.other_folder, self.other_name)
        HubsInspector.construct_dart_file(full_path)
        self.assertTrue(os.path.exists(full_path))
