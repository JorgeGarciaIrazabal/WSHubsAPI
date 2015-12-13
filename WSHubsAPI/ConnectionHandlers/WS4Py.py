import logging
from ws4py.websocket import WebSocket
from wshubsapi.CommProtocol import CommProtocol

__author__ = 'Jorge'
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class ConnectionHandler(WebSocket):
    commProtocol = CommProtocol()

    def writeMessage(self, message):
        log.debug("message to %s:\n%s" % (self._connectedClient.ID, message))
        self.send(message)

    def opened(self, *args):
        self._connectedClient = self.commProtocol.constructConnectedClient(self.writeMessage, self.close)
        clientId = int(args[0]) if len(args) > 0 else None
        self.ID = self._connectedClient.onOpen(clientId)
        log.debug("open new connection with ID: %s " % str(self.ID))

    def received_message(self, message):
        log.debug("Message received from ID: %s\n%s " % (str(self.ID), str(message)))
        self._connectedClient.onAsyncMessage(message.data)

    def closed(self, code, reason=None):
        log.debug("client closed %s" % self._connectedClient.__dict__.get("ID", "None"))
        self._connectedClient.onClosed()
