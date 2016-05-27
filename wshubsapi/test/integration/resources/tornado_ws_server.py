import importlib
import os
from os.path import join
import logging.config
import json
import sys

from tornado import web, ioloop
from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.connection_handlers.tornado_handler import ConnectionHandler

if os.path.exists('logging.json'):
    logging.config.dictConfig(json.load(open('logging.json')))
log = logging.getLogger(__name__)


def get_module_path():
    path = os.path.join(os.path.dirname(__file__))
    if not path.endswith("resources"):
        path = os.path.join(path, 'wshubsapi', 'test', 'integration', 'resources')
    return path


settings = {"static_path": join(get_module_path(), "clients_api")}

app = web.Application([
    (r'/(.*)', ConnectionHandler),
], **settings)

if __name__ == '__main__':
    # necessary to add this import for code inspection
    importlib.import_module("wshubsapi.test.integration.resources.hubs.chat_hub")
    importlib.import_module("wshubsapi.test.integration.resources.hubs.echo_hub")
    HubsInspector.inspect_implemented_hubs(force_reconstruction=True)
    HubsInspector.construct_js_file(settings["static_path"] + os.sep + "hubsApi.js")
    HubsInspector.construct_python_file(settings["static_path"] + os.sep + "hubs_api.py")
    log.debug("starting...")
    app.listen(11111)

    ioloop.IOLoop.instance().start()
