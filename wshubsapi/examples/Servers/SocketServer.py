import importlib
import json
import logging
import logging.config

import time

from wshubsapi.HubsInspector import HubsInspector
from wshubsapi.ConnectionHandlers.SocketHandler import SocketHandler

logging.config.dictConfig(json.load(open('logging.json')))
log = logging.getLogger(__name__)

if __name__ == '__main__':
    importlib.import_module("ChatHub")  # necessary to add this import for code inspection
    # construct the necessary client files in the specified path
    HubsInspector.inspectImplementedHubs()
    HubsInspector.constructPythonFile("../Clients/_static")
    HubsInspector.constructJSFile("../Clients/_static")

    server = SocketHandler("localhost", 8890)

    while True:
        time.sleep(0.1)

