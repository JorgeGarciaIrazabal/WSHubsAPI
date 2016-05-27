
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
    HubsInspector.include_hubs_in("*_hub.py")  # use glob path patterns
    HubsInspector.inspect_implemented_hubs()
    HubsInspector.construct_js_file(settings["static_path"] + os.sep + "hubsApi.js")
    HubsInspector.construct_python_file(settings["static_path"] + os.sep + "hubs_api.py")
    app.listen(8888)
    log.debug("listening...")

    ioloop.IOLoop.instance().start()
