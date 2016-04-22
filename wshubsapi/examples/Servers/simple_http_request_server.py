import SocketServer
import importlib
import logging
from wshubsapi.connection_handlers.request_handler import SimpleRequestHandler
from wshubsapi.hubs_inspector import HubsInspector

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("_server_")

httpd = SocketServer.TCPServer(("localhost", 8888), SimpleRequestHandler)

log.debug("listening...")
importlib.import_module("chat_hub")
HubsInspector.inspect_implemented_hubs()
HubsInspector.construct_js_file("../Clients/_static")
HubsInspector.construct_python_file("../Clients/_static")
httpd.serve_forever()
