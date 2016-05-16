import json
import logging.config
import sys
from wshubsapi.connection_handlers.request_handler import RequestClient
# file created by the server
from _static.hubs_api import HubsAPI

logging.config.dictConfig(json.load(open('logging.json')))

if __name__ == '__main__':
    ws = HubsAPI('http://localhost:8888/', client_class=RequestClient)
    ws.connect()
    ws.defaultOnError = lambda m: sys.stdout.write("message could not be sent!!!!! {}\n".format(m))
    name = raw_input("Enter your name:")
    print("Hello %s. You have entered in the chat room, write and press enter to send message" % name)
    while True:
        message = raw_input("")
        if sys.version_info[0] == 2:
            message = message.decode(sys.stdin.encoding)
        serverReplay = ws.ChatHub.server.send_to_all(name, message).result(timeout=30)
        print("Server reply: {}".format(serverReplay))

