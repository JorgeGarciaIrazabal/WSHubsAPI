import importlib
import json
import logging.config

from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.connection_handlers.socket_handler import create_socket_server

logging.config.dictConfig(json.load(open('logging.json')))
log = logging.getLogger(__name__)

if __name__ == '__main__':
    importlib.import_module("ChatHub")  # necessary to add this import for code inspection
    # construct the necessary client files in the specified path
    HubsInspector.inspect_implemented_hubs()
    HubsInspector.construct_python_file("../Clients/_static/hubs_api.py")

    server = create_socket_server("127.0.0.1", 8890)

    server.serve_forever()


