import SocketServer
import importlib
import logging
from wshubsapi.connection_handlers.request_handler import SimpleRequestHandler
from wshubsapi.hubs_inspector import HubsInspector

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("_server_")

httpd = SocketServer.TCPServer(("localhost", 8888), SimpleRequestHandler)

log.debug("listening...")

HubsInspector.include_hubs_in("*_hub.py")  # use glob path patterns
HubsInspector.inspect_implemented_hubs()
HubsInspector.construct_js_file("../Clients/_static/hubsApi.js")
HubsInspector.construct_python_file("../Clients/_static/hubs_api.py")
httpd.serve_forever()
