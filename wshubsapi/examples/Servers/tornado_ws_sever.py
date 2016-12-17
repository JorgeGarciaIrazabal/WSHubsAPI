import os
import logging.config
import json
from tornado import web, ioloop

from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.connection_handlers.tornado_handler import ConnectionHandler

logging.config.dictConfig(json.load(open('logging.json')))
log = logging.getLogger(__name__)

settings = {"static_path": os.path.join(os.path.dirname(__file__), "../Clients/_static")}

app = web.Application([
    (r'/(.*)', ConnectionHandler),
], **settings)

if __name__ == '__main__':
    HubsInspector.include_hubs_in("*_hub.py")  # use glob path patterns
    HubsInspector.inspect_implemented_hubs()
    HubsInspector.construct_js_file(settings["static_path"] + os.sep + "hubsApi.js")
    HubsInspector.construct_python_file(settings["static_path"] + os.sep + "hubs_api.py")
    HubsInspector.construct_dart_file(settings["static_path"] + os.sep + "hubs_api.dart")
    log.debug("starting...")
    app.listen(8888)

    ioloop.IOLoop.instance().start()
