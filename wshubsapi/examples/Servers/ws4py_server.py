from wsgiref.simple_server import make_server

from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication

from wshubsapi.connection_handlers.ws4py_handler import ConnectionHandler
from wshubsapi.hubs_inspector import HubsInspector

if __name__ == '__main__':
    HubsInspector.include_hubs_in("*_hub.py")  # use glob path patterns
    HubsInspector.inspect_implemented_hubs()  # setup api
    HubsInspector.construct_python_file("../Clients/_static/hubs_api.py")  # only if you will use a python client
    HubsInspector.construct_js_file("../Clients/_static/hubsApi.js")  # only if you will use a js client

    server = make_server('127.0.0.1', 8888, server_class=WSGIServer,
                         handler_class=WebSocketWSGIRequestHandler,
                         app=WebSocketWSGIApplication(handler_cls=ConnectionHandler))
    server.initialize_websockets_manager()
    server.serve_forever()
