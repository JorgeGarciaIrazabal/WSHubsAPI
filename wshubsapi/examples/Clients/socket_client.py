import json
import logging
import logging.config
import sys

from wshubsapi.connection_handlers.socket_handler import SocketClient

logging.config.dictConfig(json.load(open('logging.json')))
if sys.version_info[0] == 2:
    input = raw_input

# file created by the server
from _static.hubs_api import HubsAPI

if __name__ == '__main__':

    ws = HubsAPI('ws://127.0.0.1:8890/', clientClass=SocketClient)
    ws.connect()
    ws.defaultOnError = lambda m: sys.stdout.write("message could not be sent!!!!! {}\n".format(m))
    ws.UtilsAPIHub.server.set_id("testing")

    def print_message(sender_name, message):
        print(u"From {0}: {1}".format(sender_name, message))

    ws.ChatHub.client.print_message = print_message
    ws.ChatHub.server.subscribe_to_hub().done(lambda x: ws.ChatHub.server.get_subscribed_clients_to_hub())
    name = input("Enter your name:")
    #ws.server.ChatHub.getNumOfClientsConnected().done(lambda x: sys.stdout.write(x[1]+"\n"), lambda x: sys.stdout.write("Error:%s\n"%x))
    print("Hello %s. You have entered in the chat room, write and press enter to send message" % name)
    while True:
        message = input("")
        if sys.version_info[0] == 2:
            message = message.decode(sys.stdin.encoding)
        ws.ChatHub.server.send_to_all(name, message).done(lambda m: sys.stdout.write("message sent to {} client(s)\n".format(m)))
