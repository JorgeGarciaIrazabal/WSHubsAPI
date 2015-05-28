import os
import random
import string
import time
import logging
import logging.config
import json
from tornado import web, ioloop
from HubDecorator import HubDecorator
from ConnectionHandlers.Tornado import ClientHandler


logging.config.dictConfig(json.load(open('logging.json')))
log = logging.getLogger(__name__)

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "login_url": "/login",
}


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
],**settings)
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
        __HubName__ = "MyHubTest"
        def test(self, _client, a=1, b=2):
            print(a, b)

        def tast(self, _client, a=5, b=1, c=3):
            """
            @type _client: CommHandler
            """
            _client.onTest("we are onTest")
            time.sleep(a)
            #_client.otherClients.onTest(5,6)
            #_client.allClients.onTest(6,7)
            return tes()
    log.debug("starting...")
    HubDecorator.constructPythonFile()
    app.listen(8888)
    ioloop.IOLoop.instance().start()
