import importlib
import logging
import os
from tornado import web, ioloop

from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.connection_handlers.request_handler import TornadoRequestHandler

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("_serverMock_")

settings = {"static_path": os.path.join(os.path.dirname(__file__), "../Clients/_static")}

app = web.Application([
    (r'/(.*)', TornadoRequestHandler),
])

if __name__ == '__main__':
    importlib.import_module("chat_hub")
    HubsInspector.inspect_implemented_hubs()
    HubsInspector.construct_js_file(settings["static_path"])
    HubsInspector.construct_python_file(settings["static_path"])
    app.listen(8888)
    log.debug("listening...")

    ioloop.IOLoop.instance().start()
