import time

__author__ = 'Jorge'
from wsgiref.simple_server import make_server

from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler

from ws4py.server.wsgiutils import WebSocketWSGIApplication

from wshubsapi.ConnectionHandlers.WS4Py import ClientHandler
from wshubsapi.Hub import Hub

import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

def initServer():
    class BaseHub(Hub):
        def sendToAll(self, name, message):
            self.otherClients.onMessage(name,message)
            return len(self.otherClients)
        def timeout(self,timeout = 3):
            time.sleep(timeout)
            return True

    Hub.constructPythonFile("client")
    server = make_server('127.0.0.1', 8888, server_class=WSGIServer,
                         handler_class=WebSocketWSGIRequestHandler,
                         app=WebSocketWSGIApplication(handler_cls=ClientHandler))
    server.initialize_websockets_manager()
    server.serve_forever()

if __name__ == '__main__':
    initServer()