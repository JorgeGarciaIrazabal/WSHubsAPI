import importlib
import os
from os.path import join
import logging.config
import json
import sys

from tornado import web, ioloop
from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.connection_handlers.tornado_handler import ConnectionHandler

logging.config.dictConfig(json.load(open('logging.json')))
log = logging.getLogger(__name__)

settings = {"static_path": join(os.path.dirname(__file__), "clients_api")}

app = web.Application([
    (r'/(.*)', ConnectionHandler),
], **settings)

if __name__ == '__main__':
    importlib.import_module("hubs")  # necessary to add this import for code inspection
    HubsInspector.inspect_implemented_hubs()
    HubsInspector.construct_js_file(settings["static_path"])
    HubsInspector.construct_python_file(settings["static_path"])
    log.debug("starting...")
    app.listen(11111)

    ioloop.IOLoop.instance().start()
