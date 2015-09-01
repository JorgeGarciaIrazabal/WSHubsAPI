import importlib
import json
import logging
import logging.config
import threading
from wshubsapi.ConnectionHandlers.WS4Py import ClientHandler
from wsgiref.simple_server import make_server
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from wshubsapi.Hub import Hub
from ws4py.server.wsgiutils import WebSocketWSGIApplication
from wshubsapi.examples.Servers.ChatHub import ChatHub

logging.config.dictConfig(json.load(open('logging.json')))
log = logging.getLogger(__name__)

def setMessage():
    while True:
        raw_input("test")
        ChatHub.sendToAll("test", "testMessage")

if __name__ == '__main__':
    # construct the necessary client files in the specified path
    Hub.constructPythonFile("../Clients/_static")
    Hub.constructJSFile("../Clients/_static")
    # Hub.constructJAVAFile("tornado.WSHubsApi", "../Clients/_static")

    server = make_server('127.0.0.1', 8888, server_class=WSGIServer,
                         handler_class=WebSocketWSGIRequestHandler,
                         app=WebSocketWSGIApplication(handler_cls=ClientHandler))
    server.initialize_websockets_manager()
    #ChatHub.sendToAll("test", "testMessage")
    t = threading.Thread(target=setMessage)
    t.start()
    log.debug("starting...")
    target = server.serve_forever()
