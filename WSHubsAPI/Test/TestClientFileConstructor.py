import os
from os.path import isfile
from WSHubsAPI.ClientFileGenerator.JAVAFileGenerator import JAVAFileGenerator
from WSHubsAPI.ClientFileGenerator.JSClientFileGenerator import JSClientFileGenerator
from WSHubsAPI.ClientFileGenerator.PythonClientFileGenerator import PythonClientFileGenerator
from WSHubsAPI.Hub import Hub
from os import listdir

import unittest

class TestHubDetection(unittest.TestCase):
    def setUp(self):
        class TestHub(Hub):
            def getData(self):
                pass

        class TestHub2(Hub):
            pass

        Hub.initHubsInspection()

    def test_JSCreation(self):
        Hub.constructJSFile()
        self.assertTrue(os.path.exists(JSClientFileGenerator.FILE_NAME))
        os.remove(JSClientFileGenerator.FILE_NAME)

        otherPath = "onTest"
        fullPath = os.path.join(otherPath, JSClientFileGenerator.FILE_NAME)
        Hub.constructJSFile(otherPath)
        self.assertTrue(os.path.exists(fullPath))
        os.remove(fullPath)
        os.removedirs("onTest")

    def test_JAVACreation(self):
        path = "onTest"
        Hub.constructJAVAFile("test", path, createClientTemplate=True)
        self.assertTrue(os.path.exists(os.path.join(path, JAVAFileGenerator.SERVER_FILE_NAME)))
        self.assertTrue(os.path.exists(os.path.join(path, JAVAFileGenerator.CLIENT_FILE_NAME)))
        for f in listdir(path):
            fullPath = os.path.join(path, f)
            os.remove(fullPath)
        os.removedirs(path)

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
        os.remove(fullPath)
        os.remove(packageFilePath)
        os.removedirs("onTest")

if __name__ == '__main__':
    unittest.main()
