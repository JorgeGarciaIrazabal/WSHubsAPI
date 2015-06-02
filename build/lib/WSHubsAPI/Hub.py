import inspect
from WSHubsAPI.ClientFileGenerator.JAVAFileGenerator import JAVAFileGenerator
from WSHubsAPI.ClientFileGenerator.JSClientFileGenerator import JSClientFileGenerator
from WSHubsAPI.ClientFileGenerator.PythonClientFileGenerator import PythonClientFileGenerator
from WSHubsAPI.utils import classproperty

__author__ = 'Jorge'

class HubException(Exception):
    pass

class Hub(object):
    HUBs_DICT = {}
    __hubsConstructed = False
    @classmethod
    def initHubsInspection(cls):
        if not cls.__hubsConstructed:
            for c in Hub.__subclasses__():
                try:
                    c()
                except TypeError as e:
                    if "__init__() takes" in str(e):
                        raise HubException("Hubs can not have a constructor with parameters. Check Hub: %s" % c.__name__)
                    else:
                        raise e
            cls.__hubsConstructed = True
    @classmethod
    def constructJSFile(cls, path=""):
        cls.initHubsInspection()
        JSClientFileGenerator.createFile(path, cls.HUBs_DICT.values())

    @classmethod
    def constructJAVAFile(cls, path, package, createClientTemplate = False):
        cls.initHubsInspection()
        hubs=cls.HUBs_DICT.values()
        JAVAFileGenerator.createFile(path, package, hubs)
        if createClientTemplate:
            JAVAFileGenerator.createClientTemplate(path,package,hubs)

    @classmethod
    def constructPythonFile(cls, path="."):
        cls.initHubsInspection()
        PythonClientFileGenerator.createFile(path, cls.HUBs_DICT.values())

    @property
    def sender(self):
        """
        :rtype : CommHandler
        """
        frame = inspect.currentframe()
        while frame.f_back is not None:
            frame = frame.f_back
            if isinstance(frame.f_locals.get("self",None), CommHandler):
                return frame.f_locals["self"]
        return None

    @property
    def allClients(self):
        connection = self.sender
        return ConnectionGroup(connection.connections.values())

    @property
    def otherClients(self):
        connection = self.sender
        return ConnectionGroup(filter(lambda x: x.ID != connection.ID, connection.connections.values()))


    def getClients(self, function):
        connection = self.sender
        return ConnectionGroup(filter(function, connection.connections.values()))

    def __init__(self):
        hubName = self.__class__.__dict__.get("__HubName__", self.__class__.__name__)
        if hubName in self.HUBs_DICT:
            raise HubException("Hub's name must be unique")
        setattr(self.__class__, "__HubName__", hubName)
        try:
            self.HUBs_DICT[hubName] = self
        except TypeError as e:
            if "__init__() takes" in str(e):
                raise HubException("Hubs can not have a constructor with parameters. Check Hub: %s" % self.__class__.__name__)
            else:
                raise e



from WSHubsAPI.CommProtocol import ConnectionGroup, CommHandler