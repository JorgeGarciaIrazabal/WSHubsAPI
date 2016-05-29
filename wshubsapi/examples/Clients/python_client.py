from __future__ import print_function
import json
import logging.config
import sys
# file created by the server
from _static.hubs_api import HubsAPI


logging.config.dictConfig(json.load(open('logging.json')))
if sys.version_info[0] == 2:
    input = raw_input


if __name__ == '__main__':
    ws = HubsAPI('ws://127.0.0.1:8888/')
    ws.connect()
    ws.defaultOnError = lambda m: print("message could not be sent!!!!! {}\n".format(m))
    ws.UtilsAPIHub.server.set_id("testing")

    class ChatHubClient(HubsAPI.ChatHubClass.ClientClass):
        def print_message(self, sender_name, msg):
            print(u"From {0}: {1}".format(sender_name, msg))


    ws.ChatHub.client = ChatHubClient()
    ids = ws.ChatHub.server.get_subscribed_clients_ids().result()
    result = ws.ChatHub.get_clients("jsClient").print_message("test1", "test2").result()
    name = input("Enter your name:")
    # ws.ChatHub.server.get_subscribed_clients_to_hub() \
    #     .done(lambda x: sys.stdout.write(x[1] + "\n"), lambda x: sys.stdout.write("Error:%s\n" % x))
    print("Hello %s. You have entered in the chat room, write and press enter to send message" % name)
    while True:
        message = input("")
        if sys.version_info[0] == 2:
            message = message.decode(sys.stdin.encoding)
        message_from_server = ws.ChatHub.server.send_to_all(name, message).result()
        print("message sent to {} client(s)\n".format(message_from_server))
