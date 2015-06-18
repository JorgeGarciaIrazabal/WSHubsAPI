import json
import logging
import logging.config
import sys

logging.config.dictConfig(json.load(open('logging.json')))

# file created by the server
from _static.WSHubsApi import HubsAPI

if __name__ == '__main__':
    ws = HubsAPI('ws://127.0.0.1:8888')
    ws.connect()

    def printMessage(senderName, message):
        print(u"From {0}: {1}".format(senderName, message))

    ws.ChatHub.client.onMessage = printMessage
    name = raw_input("enter your name:")
    #ws.server.ChatHub.getNumOfClientsConnected().done(lambda x: print(x[1]), lambda x: print("Error:%s"%x))
    print("Hello %s. You have entered in the chat room, write and press enter to send message" % name)
    while True:
        message = raw_input("")
        ws.ChatHub.server.sendToAll(name, message).done(lambda m: sys.stdout.write("message sent to %d client(s)\n"%m),
                                                        lambda m: sys.stdout.write("!!!!!message not sent!!!!!\n"))
