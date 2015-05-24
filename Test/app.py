import logging
import logging.config
import json
import threading
import unittest
import os
import time

from ClientHandlers import web, ioloop

from CommProtocol import ClientHandler
from HubDecorator import HubDecorator

logging.config.dictConfig(json.load(open('logging.json')))

log = logging.getLogger(__name__)

class

class IndexHandler(web.RequestHandler):
    def get(self):
        self.render("index.html")

class TestJSClient(unittest.TestCase):
    JS_PATH = "JSClient/"
    def setUp(self):
        HubDecorator.constructJSFile(self.JS_PATH)

    def testFileConstructor(self):
        self.assertTrue(os.path.isfile(self.JS_PATH+HubDecorator.JS_FILE_NAME))

    def testClientConnection(self):
        os.system("start "+self.JS_PATH+"index.html")
        time.sleep(10)#wait for web explorer to open
        self.assertIn(12345, ClientHandler.clients)



def initServer():
    app = web.Application([
    (r'/', IndexHandler),
    (r'/ws/(.*)', ClientHandler),
    ])

    app.listen(8888)
    log.debug("starting...")
    ioloop.IOLoop.instance().start()
    print("error")

t = threading.Thread(target=initServer)
t.setDaemon(True)
t.start()

if __name__ == '__main__':
    unittest.main()