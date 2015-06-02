import json
import logging
import logging.config
from threading import Thread
import time
from WSHubsAPI.ConnectionHandlers.WS4Py import ClientHandler
from wsgiref.simple_server import make_server
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from WSHubsAPI.Hub import Hub
from ws4py.server.wsgiutils import WebSocketWSGIApplication

logging.config.dictConfig(json.load(open('logging.json')))
log = logging.getLogger(__name__)

if __name__ == '__main__':
    import ChatHub #necessaty to add this imput for code inspection
    Hub.constructPythonFile("../Clients/_static")
    Hub.constructJSFile("../Clients/_static")

    server = make_server('127.0.0.1', 8888, server_class=WSGIServer,
                     handler_class=WebSocketWSGIRequestHandler,
                     app=WebSocketWSGIApplication(handler_cls=ClientHandler))
    server.initialize_websockets_manager()
    log.debug("starting...")
    target=server.serve_forever()


