import logging
from ws4py.websocket import WebSocket
from wshubsapi.CommProtocol import CommHandler

__author__ = 'Jorge'
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class ClientHandler(WebSocket):
    def writeMessage(self, message):
        log.debug("message to %s:\n%s" % (self._commHandler.ID, message))
        self.send(message)

    def opened(self, *args):
        self._commHandler = CommHandler(self)
        self._commHandler.writeMessage = self.writeMessage
        id = int(args[0]) if len(args)>0 else None
        self.ID = self._commHandler.onOpen(id)
        log.debug("open new connection with ID: %s " % str(self.ID))

    def received_message(self, message):
        log.debug("Message received from ID: %s\n%s " % (str(self.ID), str(message)))
        self._commHandler.onAsyncMessage(message.data)

    def closed(self, code, reason = None):
        log.debug("client closed %s" % self._commHandler.__dict__.get("ID", "None"))
        self._commHandler.onClose()

