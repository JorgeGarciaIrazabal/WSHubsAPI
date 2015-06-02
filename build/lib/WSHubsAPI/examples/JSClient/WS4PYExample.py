import json
import logging

from ConnectionHandlers.WS4Py import ClientHandler
from HubDecorator import HubDecorator
import time
import cherrypy
from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool

__author__ = 'jgarc'


logging.config.dictConfig(json.load(open('logging.json')))
log = logging.getLogger(__name__)


class Root(object):
    @cherrypy.expose
    def index(self):
        pass

if __name__ == '__main__':
    @HubDecorator.hub
    class TestClass2:

        def test(self, _client, a=1, b=2):
            time.sleep(b)
            return a, b

        def tast(self, _client, a=5, b=1, c=3):
            print(a, b)

    @HubDecorator.hub
    class TestClass:

        def test(self, _client, a=1, b=2):
            print(a, b)

        def tast(self, _client, a=5, b=1, c=3):
            """
            @type _client: CommHandler
            """
            time.sleep(a)
            _client.onTest(5,6)
            #_client.otherClients.onTest(5,6) #todo: not implemented respond on client
            #_client.allClients.onTest(6,7)
            return {1:1,2:2}

    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                            'server.socket_port': 8888,
                            'engine.autoreload_on': False})
    WebSocketPlugin(cherrypy.engine).subscribe()
    cherrypy.tools.websocket = WebSocketTool()

    config = {
        '/': {
            'tools.websocket.on': True,
            'tools.websocket.handler_cls': ClientHandler
        }
    }
    cherrypy.quickstart(Root(), '/', config)


