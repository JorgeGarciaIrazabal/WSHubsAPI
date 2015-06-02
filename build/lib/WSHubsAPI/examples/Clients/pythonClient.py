import json
import logging
from _static.WSProtocol import WSConnection

log = logging.getLogger(__name__)

if __name__ == '__main__':
    import logging.config

    logging.config.dictConfig(json.load(open('logging.json')))
    global ws
    ws = WSConnection.init('ws://127.0.0.1:8888')
    ws.connect()
    def printMessage(senderName, message):
        print(u"From {0}: {1}".format(senderName,message))
    ws.client.ChatHub.onMessage = printMessage
    name = raw_input("enter your name:")
    #ws.server.ChatHub.getNumOfClientsConnected().done(lambda x: print(x[1]), lambda x: print("Error:%s"%x))
    print("Hello %s. You have entered in the chat room, write and press enter to send message"%name)
    while True:
        message = raw_input("")
        ws.server.ChatHub.sendToAll(name,message)

