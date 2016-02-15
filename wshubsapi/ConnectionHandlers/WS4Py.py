import logging
from ws4py.websocket import WebSocket
from wshubsapi.ConnectedClient import ConnectedClient

from wshubsapi.CommEnvironment import CommEnvironment

__author__ = 'Jorge'
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class ConnectionHandler(WebSocket):
    commEnvironment = None

    def __init__(self, sock, protocols=None, extensions=None, environ=None, heartbeat_freq=None):
        super(ConnectionHandler, self).__init__(sock, protocols, extensions, environ, heartbeat_freq)
        if ConnectionHandler.commEnvironment is None:
            ConnectionHandler.commEnvironment = CommEnvironment()
        self._connectedClient = ConnectedClient(self.commEnvironment, self.writeMessage)

    def writeMessage(self, message):
        self.send(message)
        log.debug("message to %s:\n%s" % (self._connectedClient.ID, message))

    def opened(self, *args):
        try:
            clientId = int(args[0])
        except:
            clientId = None
        ID = self.commEnvironment.onOpen(self._connectedClient, clientId)
        log.debug("open new connection with ID: {} ".format(ID))

    def received_message(self, message):
        log.debug("Message received from ID: %s\n%s " % (str(self._connectedClient.ID), str(message)))
        self.commEnvironment.onAsyncMessage(self._connectedClient, message.data)

    def closed(self, code, reason=None):
        log.debug("client closed %s" % self._connectedClient.__dict__.get("ID", "None"))
        self.commEnvironment.onClosed(self._connectedClient)
