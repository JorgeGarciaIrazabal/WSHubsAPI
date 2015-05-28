from __future__ import print_function
import json
import logging
import time
from WSProtocol import WSConnection
log = logging.getLogger(__name__)


if __name__ == '__main__':
    import logging.config
    logging.config.dictConfig(json.load(open('logging.json')))
    global ws
    try:
        ws = WSConnection.init('ws://localhost:8888/ws/12345')
        ws.connect()
        ws.client.MyHubTest.onTest = lambda x:print(str(x))
        ws.server.MyHubTest.tast(2).done(lambda x: print(str(x)), lambda x: print(x))
        for i in range(190):
            time.sleep(1)
    except KeyboardInterrupt:
        ws.close()