import importlib
import json
from wshubsapi.HubsInspector import HubsInspector
from wshubsapi.ConnectionHandlers.WS4Py import ConnectionHandler
from wsgiref.simple_server import make_server
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication
import logging
import logging.config

logging.config.dictConfig(json.load(open('logging.json')))
log = logging.getLogger(__name__)

if __name__ == '__main__':
    importlib.import_module("ChatHub")  # necessary to add this import for code inspection
    importlib.import_module("DB_API")  # necessary to add this import for code inspection
    # construct the necessary client files in the specified path
    HubsInspector.inspect_implemented_hubs()
    HubsInspector.construct_python_file()
    # Hub.constructJAVAFile("tornado.WSHubsApi", "../Clients/_static") in beta
    # HubsInspector.constructCppFile("../Clients/_static") in alpha

    server = make_server('127.0.0.1', 8888, server_class=WSGIServer,
                         handler_class=WebSocketWSGIRequestHandler,
                         app=WebSocketWSGIApplication(handler_cls=ConnectionHandler))
    server.initialize_websockets_manager()

    log.debug("starting...")
    target = server.serve_forever()
