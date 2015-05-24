import os
import random
import string
import time
from tornado import websocket, web, ioloop
import logging
import logging.config
import json
from HubDecorator import HubDecorator
logging.config.dictConfig(json.load(open('logging.json')))
from CommProtocol import ClientHandler,CommHandler

cl = []
log = logging.getLogger(__name__)

class IndexHandler(web.RequestHandler):
    def get(self):
        self.render("index.html")

class UploadHandler(web.RequestHandler):
    def post(self):
        file1 = self.request.files['filearg'][0]
        original_fname = file1['filename']
        extension = os.path.splitext(original_fname)[1]
        fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        final_filename= fname+extension
        output_file = open(final_filename, 'w')
        output_file.write(file1['body'])
        self.finish("file" + final_filename + " is uploaded")

app = web.Application([
    (r'/', IndexHandler),
    (r'/ws/(.*)', ClientHandler),
    (r'/upload', UploadHandler),
])
class tes:
    def __init__(self):
        self.a = 10
        self.b =20

if __name__ == '__main__':
    @HubDecorator.hub
    class TestClass2:

        def test(self, _client, a=1, b=2):
            print(b)
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
            clients = _client.OtherClients()
            _client.onTest(5,6)
            """for c in clients:
                print(c.ID)
                c.onTest(5,6)"""
            return tes()
    HubDecorator.constructJSFile("Test/JSClient/")
    #HubDecorator.constructJAVAFile("C:/Users/jgarc/workspace/tornado/src/tornado", "tornado")
    log.debug("starting...")
    app.listen(8888)
    ioloop.IOLoop.instance().start()