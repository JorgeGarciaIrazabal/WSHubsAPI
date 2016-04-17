import json
import logging.config
import sys
import time

from wshubsapi.connection_handlers.request_handler import RequestClient
# file created by the server
from _static.hubs_api import HubsAPI

logging.config.dictConfig(json.load(open('logging.json')))
if sys.version_info[0] == 2:
    input = raw_input


if __name__ == '__main__':
    ws = HubsAPI('http://localhost:8000/test/', client_class=RequestClient)
    ws.connect()
    ws.defaultOnError = lambda m: sys.stdout.write("message could not be sent!!!!! {}\n".format(m))
    name = input("Enter your name:")
    print("Hello %s. You have entered in the chat room, write and press enter to send message" % name)
    while True:
        message = input("")
        if sys.version_info[0] == 2:
            message = message.decode(sys.stdin.encoding)
        futures = []
        for i in range(1):
            futures.append(ws.ChatHub.server.send_to_all(name, message))
        responses = [f.result() for f in futures]
        for i, r in enumerate(responses):
            print i, r
