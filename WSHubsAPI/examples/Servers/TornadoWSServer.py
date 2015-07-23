import importlib
import os
import logging
import logging.config
import json

from tornado import web, ioloop

from WSHubsAPI.Hub import Hub
from WSHubsAPI.ConnectionHandlers.Tornado import ClientHandler

logging.config.dictConfig(json.load(open('logging.json')))
log = logging.getLogger(__name__)

settings = {"static_path": os.path.join(os.path.dirname(__file__), "../Clients/_static"), }

app = web.Application([
    (r'/(.*)', ClientHandler),
], **settings)

if __name__ == '__main__':
    importlib.import_module("ChatHub")  # necessary to add this import for code inspection

    Hub.constructJSFile(settings["static_path"])
    Hub.constructPythonFile(settings["static_path"])
    log.debug("starting...")
    app.listen(8888)

    ioloop.IOLoop.instance().start()
