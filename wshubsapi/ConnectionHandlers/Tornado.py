import logging
from wshubsapi.CommEnvironment import CommEnvironment
import tornado.websocket

__author__ = 'Jorge'
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class ConnectionHandler(tornado.websocket.WebSocketHandler):
    commEnvironment = None

    def __init__(self, application, request, **kwargs):
        super(ConnectionHandler, self).__init__(application, request, **kwargs)
        if ConnectionHandler.commEnvironment is None:
            ConnectionHandler.commEnvironment = CommEnvironment()
        self._connectedClient = self.commEnvironment.constructConnectedClient(self.writeMessage)


    def data_received(self, chunk):
        pass

    def writeMessage(self, message):
        log.debug("message to %s:\n%s" % (self._connectedClient.ID, message))
        self.write_message(message)

    def open(self, *args):
        try:
            clientId = int(args[0])
        except:
            clientId = None
        ID = self._connectedClient.onOpen(clientId)
        log.debug("open new connection with ID: {} ".format(ID))

    def on_message(self, message):
        log.debug("Message received from ID: {}\n{} ".format(self._connectedClient.ID, message))
        self._connectedClient.onAsyncMessage(message)

    def on_close(self):
        log.debug("client closed %s" % self._connectedClient.__dict__.get("ID", "None"))
        self._connectedClient.onClosed()

    def check_origin(self, origin):
        return True
