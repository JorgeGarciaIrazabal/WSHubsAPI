import inspect
import logging
import logging.config
import logging.config

from ClientFileGenerator.JAVAFileGenerator import JAVAFileGenerator
from ClientFileGenerator.PythonClientFileGenerator import PythonClientFileGenerator
from ClientFileGenerator.JSClientFileGenerator import JSClientFileGenerator


log = logging.getLogger(__name__)

class HubException(Exception):
    pass

class HubDecorator:
    HUBs_DICT = {}
    IS_HUB_PROPERTY_STR = "is_a_hub_class"

    @classmethod
    def isHub(cls, obj):
        try:
            return obj.__dict__.get(cls.IS_HUB_PROPERTY_STR, False)
        except:
            return False

    @classmethod
    def constructJSFile(cls, path=""):
        JSClientFileGenerator.createFile(path, cls.HUBs_DICT.values())

    @classmethod
    def constructJAVAFile(cls, path, package, createClientTemplate = False):
        hubs=cls.HUBs_DICT.values()
        JAVAFileGenerator.createFile(path, package, hubs)
        if createClientTemplate:
            JAVAFileGenerator.createClientTemplate(path,package,hubs)

    @classmethod
    def constructPythonFile(cls, path=""):
        PythonClientFileGenerator.createFile(path, cls.HUBs_DICT.values())

    @staticmethod #todo, check if this works
    def getConnection():
        """
        :rtype : CommHandler
        """
        frame = inspect.currentframe().f_back.f_back
        return frame.f_locals["self"].connection
    #todo, could be interesting to have a getMessage like getConnection

    @staticmethod
    def hub(class_):
        setattr(class_, HubDecorator.IS_HUB_PROPERTY_STR, True)
        hubName = class_.__dict__.get("__HubName__", class_.__name__)
        if hubName in HubDecorator.HUBs_DICT:
            raise HubException("Hub's name must be unique")
        setattr(class_, "__HubName__", hubName)
        try:
            HubDecorator.HUBs_DICT[hubName] = class_()
        except TypeError as e:
            if "__init__() takes" in str(e):
                raise HubException("Hubs can not have a constructor with parameters. Check Hub: %s" % class_.__name__)
            else:
                raise e
        return class_


from CommProtocol import CommHandler

if __name__ == '__main__':
    @HubDecorator.hub
    class TestClass:
        __HubName__ = "HubName"

        def test(self, a="hola", b=2):
            print(a, b)

        def tast(self, a=5, b=1, c=3):
            print(a, b)

    @HubDecorator.hub
    class TestClass2:
        def test(self, a=1, b=2):
            print(a, b)

        def tast(self, a=5, b=1, c=3):
            print(a, b)

    HubDecorator.constructJAVAFile("", "Tornado", True)
    # HubDecorator.constructPythonFile("")
    #HubDecorator.constructJSFile()
