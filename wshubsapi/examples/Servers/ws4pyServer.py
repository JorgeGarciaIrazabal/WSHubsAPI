from wshubsapi.HubsInspector import HubsInspector
from wshubsapi.ConnectionHandlers.WS4Py import ConnectionHandler
from wsgiref.simple_server import make_server
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from wshubsapi.Hub import Hub
from ws4py.server.wsgiutils import WebSocketWSGIApplication
if __name__ == '__main__':

    class ChatHub(Hub):
        def sendToAll(self, name, message):
            allConnectedClients = self._getClientsHolder().getAllClients()
            #onMessage function has to be defined in the client side
            allConnectedClients.onMessage(name, message)
            return "Sent to %d clients" % len(allConnectedClients)

    HubsInspector.inspectImplementedHubs() #setup api
    HubsInspector.constructPythonFile("_static") #only if you will use a python client
    HubsInspector.constructJSFile("_static") #only if you will use a js client
    server = make_server('127.0.0.1', 8888, server_class=WSGIServer,
                         handler_class=WebSocketWSGIRequestHandler,
                         app=WebSocketWSGIApplication(handler_cls=ConnectionHandler))
    server.initialize_websockets_manager()
    server.serve_forever()