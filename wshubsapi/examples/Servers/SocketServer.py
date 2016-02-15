import importlib
import json
import logging
import logging.config

from wshubsapi.HubsInspector import HubsInspector
from wshubsapi.ConnectionHandlers.SocketHandler import createSocketServer

logging.config.dictConfig(json.load(open('logging.json')))
log = logging.getLogger(__name__)

if __name__ == '__main__':
    importlib.import_module("ChatHub")  # necessary to add this import for code inspection
    # construct the necessary client files in the specified path
    HubsInspector.inspectImplementedHubs()
    HubsInspector.constructPythonFile("../Clients/_static")

    server = createSocketServer("127.0.0.1", 8890)

    server.serve_forever()


