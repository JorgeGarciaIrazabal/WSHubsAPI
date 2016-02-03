import inspect

from wshubsapi.ClientFileGenerator.CppFileGenerator import CppFileGenerator
from wshubsapi.ClientFileGenerator.JAVAFileGenerator import JAVAFileGenerator
from wshubsapi.ClientFileGenerator.JSClientFileGenerator import JSClientFileGenerator
from wshubsapi.ClientFileGenerator.PythonClientFileGenerator import PythonClientFileGenerator
from wshubsapi.utils import isFunctionForWSClient, getArgs, getDefaults


class HubsInspectorException(Exception):
    pass


class HubsInspector:
    __hubsConstructed = False
    HUBs_DICT = {}

    @classmethod
    def inspectImplementedHubs(cls, forceReconstruction=False):
        if not cls.__hubsConstructed or forceReconstruction:
            cls.HUBs_DICT.clear()
            for hubClass in Hub.__subclasses__():
                try:
                    hubClass()
                except TypeError as e:
                    if "__init__()" in str(e):
                        raise HubsInspectorException(
                            "Hubs can not have a constructor with parameters. Check Hub: %s" % hubClass.__name__)
                    else:
                        raise e
            cls.__hubsConstructed = True

    @classmethod
    def constructJSFile(cls, path="."):
        cls.inspectImplementedHubs()
        JSClientFileGenerator.createFile(path, cls.getHubsInformation())

    @classmethod
    def constructJAVAFile(cls, package, path="."):
        cls.inspectImplementedHubs()
        hubs = cls.HUBs_DICT.values()
        JAVAFileGenerator.createFile(path, package, hubs)
        JAVAFileGenerator.createClientTemplate(path, package, hubs)

    @classmethod
    def constructPythonFile(cls, path="."):
        cls.inspectImplementedHubs()
        PythonClientFileGenerator.createFile(path, cls.HUBs_DICT.values())

    @classmethod
    def constructCppFile(cls, path="."):
        cls.inspectImplementedHubs()
        CppFileGenerator.createFile(path, cls.getHubsInformation())

    @classmethod
    def getHubInstance(cls, hub):
        """
        :rtype: Hub
        """
        if not isinstance(hub, basestring):
            hub = hub.__HubName__
        return cls.HUBs_DICT[hub]

    @classmethod
    def getHubsInformation(cls):
        infoReport = {}
        hubs = cls.HUBs_DICT.values()
        for hub in hubs:
            functions = inspect.getmembers(hub, predicate=isFunctionForWSClient)
            serverMethods = {}
            for name, method in functions:
                argsDict = dict(args=getArgs(method),
                                defaults = getDefaults(method))
                serverMethods[name] = argsDict
            clientMethods = {}
            for name, method in hub.clientFunctions.items():
                argsDict = dict(args=getArgs(method),
                                defaults = getDefaults(method))
                clientMethods[name] = argsDict

            infoReport[hub.__HubName__] = dict(serverMethods=serverMethods,
                                               clientMethods=clientMethods)
        return infoReport


from wshubsapi.Hub import Hub