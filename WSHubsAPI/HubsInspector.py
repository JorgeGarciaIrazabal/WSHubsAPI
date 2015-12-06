from WSHubsAPI.ClientFileGenerator.JAVAFileGenerator import JAVAFileGenerator
from WSHubsAPI.ClientFileGenerator.JSClientFileGenerator import JSClientFileGenerator
from WSHubsAPI.ClientFileGenerator.PythonClientFileGenerator import PythonClientFileGenerator
from WSHubsAPI.ConnectedClientsHolder import ConnectedClientsHolder
from WSHubsAPI.Hub import Hub


class HubsInspectorException(Exception):
    pass


class HubsInspector:
    __hubsConstructed = False

    @classmethod
    def InspectImplementedHubs(cls, forceReconstruction=False):
        if not cls.__hubsConstructed or forceReconstruction:
            Hub.HUBs_DICT.clear()
            for hubClass in Hub.__subclasses__():
                try:
                    hub = hubClass()
                    hub.setClientsHolder(ConnectedClientsHolder(hubClass.__name__))
                except TypeError as e:
                    if "__init__()" in str(e):
                        raise HubsInspectorException(
                            "Hubs can not have a constructor with parameters. Check Hub: %s" % hubClass.__name__)
                    else:
                        raise e
            cls.__hubsConstructed = True

    @classmethod
    def constructJSFile(cls, path="."):
        cls.InspectImplementedHubs()
        JSClientFileGenerator.createFile(path, Hub.HUBs_DICT.values())

    @classmethod
    def constructJAVAFile(cls, package, path="."):
        cls.InspectImplementedHubs()
        hubs = Hub.HUBs_DICT.values()
        JAVAFileGenerator.createFile(path, package, hubs)
        JAVAFileGenerator.createClientTemplate(path, package, hubs)

    @classmethod
    def constructPythonFile(cls, path="."):
        cls.InspectImplementedHubs()
        PythonClientFileGenerator.createFile(path, Hub.HUBs_DICT.values())
