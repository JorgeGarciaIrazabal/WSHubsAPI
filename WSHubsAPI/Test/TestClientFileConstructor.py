import os
from os.path import isfile
import shutil
from wshubsapi.ClientFileGenerator.JAVAFileGenerator import JAVAFileGenerator
from wshubsapi.ClientFileGenerator.JSClientFileGenerator import JSClientFileGenerator
from wshubsapi.ClientFileGenerator.PythonClientFileGenerator import PythonClientFileGenerator
from wshubsapi.Hub import Hub
from os import listdir

import unittest


class TestHubDetection(unittest.TestCase):
    def setUp(self):
        class TestHub(Hub):
            def getData(self):
                pass

        class TestHub2(Hub):
            def getData(self):
                pass

        Hub.initHubsInspection()

    def tearDown(self):
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
        Hub.constructJSFile()
        self.assertTrue(os.path.exists(JSClientFileGenerator.FILE_NAME))
        os.remove(JSClientFileGenerator.FILE_NAME)

        otherPath = "onTest"
        fullPath = os.path.join(otherPath, JSClientFileGenerator.FILE_NAME)
        Hub.constructJSFile(otherPath)
        self.assertTrue(os.path.exists(fullPath))

    def test_JAVACreation(self):
        path = "onTest"
        try:
            Hub.constructJAVAFile("test", path)
            self.assertTrue(os.path.exists(os.path.join(path, JAVAFileGenerator.SERVER_FILE_NAME)))
            self.assertTrue(os.path.exists(os.path.join(path, JAVAFileGenerator.CLIENT_PACKAGE_NAME)))
        finally:
            for f in listdir(path):
                fullPath = os.path.join(path, f)
                os.remove(fullPath) if os.path.isfile(fullPath) else shutil.rmtree(fullPath)

    def test_PythonCreation(self):
        Hub.constructPythonFile()
        self.assertTrue(os.path.exists(PythonClientFileGenerator.FILE_NAME))
        self.assertTrue(os.path.exists("__init__.py"), "Check if python package is created")
        os.remove(PythonClientFileGenerator.FILE_NAME)

        otherPath = "onTest"
        fullPath = os.path.join(otherPath, PythonClientFileGenerator.FILE_NAME)
        packageFilePath = os.path.join(otherPath, "__init__.py")
        Hub.constructPythonFile(otherPath)
        self.assertTrue(os.path.exists(fullPath))
        self.assertTrue(os.path.exists(packageFilePath), "Check if python package is created")

if __name__ == '__main__':
    unittest.main()
