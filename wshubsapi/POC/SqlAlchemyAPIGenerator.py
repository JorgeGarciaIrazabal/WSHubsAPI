import importlib
import os
from sqlalchemy import create_engine
import tables
from wshubsapi.HubsInspector import HubsInspector


class SqlAlchemyAPIGenerator:
    HUB_NAME_TEMPLATE = "DB_{0}Hub"

    def __init__(self, declarativeBase, engine, hubNameTemplate=HUB_NAME_TEMPLATE):
        """
        :type declarativeBase: sqlalchemy.ext.declarative.api.DeclarativeMeta
        """
        self.declarativeBase = declarativeBase
        self.engine = engine
        self.hubNameTemplate = hubNameTemplate

    def generateAPI(self, path="DB_API"):
        if not os.path.exists(path):
            os.makedirs(path)
        originalPath = os.getcwd()
        os.chdir(path)
        try:
            with open("__init__.py", "w") as initFile:
                initFile.write("import {}\n".format("RelationalDBHub"))
                for t in self.declarativeBase.__subclasses__():
                    hubName = self.hubNameTemplate.format(t.__name__)
                    with open(hubName + ".py", "w") as f:
                        f.write("""
from wshubsapi.POC.RelationalDBHub import RelationalDBHub


class {0}(RelationalDBHub):
    def __init__(self):
        super({0}, self).__init__()

    # automatically created methods "insert", "update", "delete", "selectID", "select"
    # create here more methods to extend the api
""".format(hubName))

                    initFile.write("import {}\n".format(hubName))
        finally:
            os.chdir(originalPath)

    def initializeDBHubs(self):
        for t in self.declarativeBase.__subclasses__():
            hubName = self.hubNameTemplate.format(t.__name__)
            hubClassInstance = importlib.import_module("DB_API.{}".format(hubName)).__dict__[hubName]
            hub = HubsInspector.get_hub_instance(hubClassInstance)
            hub.engine = self.engine
            hub.entryTable = t


if __name__ == '__main__':
    gen = SqlAlchemyAPIGenerator(tables.SqlTableEntity, create_engine("mysql://root@localhost/APITest?charset=utf8", echo=True))
    gen.generateAPI()
