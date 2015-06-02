from __future__ import print_function
import json
import logging
from WSHubsAPI.WSProtocol import WSConnection

log = logging.getLogger(__name__)

if __name__ == '__main__':
    import logging.config

    logging.config.dictConfig(json.load(open('logging.json')))
    global ws
    try:
        ws = WSConnection.init('ws://localhost:8888/ws/12345')
        ws.connect()
        ws.client.ChatHub.alert = lambda x: print(str(x))
        ws.server.ChatHub.getNumOfClientsConnected().done(lambda x: print(x[1]), lambda x: print(x))
        while True:
            message = input("")
            ws.server.ChatHub.sendToAll(message)
    except KeyboardInterrupt:
        ws.close()
