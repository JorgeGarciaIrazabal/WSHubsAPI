import json
import logging.config
import os

from flask import Flask
from flask import request
from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.connection_handlers.request_handler import FlaskRequestHandler

logging.config.dictConfig(json.load(open('logging.json')))
log = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/api', methods=['GET'])
def api_handle():
    handler = FlaskRequestHandler()
    handler.handle_message()
    return handler.get_response()


if __name__ == '__main__':
    HubsInspector.include_hubs_in("*_hub.py")  # use glob path patterns
    HubsInspector.inspect_implemented_hubs()
    HubsInspector.construct_js_file("../Clients/_static" + os.sep + "hubsApi.js")
    HubsInspector.construct_python_file("../Clients/_static" + os.sep + "hubs_api.py")
    log.debug("listening...")
    app.run(port=8888, processes=50)
