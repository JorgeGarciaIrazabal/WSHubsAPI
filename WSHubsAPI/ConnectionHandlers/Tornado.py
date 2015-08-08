import logging
from wshubsapi.CommProtocol import CommHandler
import tornado.websocket
from wshubsapi.ValidateStrings import getUnicode

__author__ = 'Jorge'
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class ClientHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        super(ClientHandler, self).__init__(application, request, **kwargs)
        self._commHandler = CommHandler(self)
        self._commHandler.writeMessage = self.writeMessage
        self.ID = None

    def writeMessage(self, message):
        log.debug("message to %s:\n%s" % (self._commHandler.ID, message))
        self.write_message(message)

    def open(self, *args):
        try:
            id = int(args[0])
        except:
            id = None
        self.ID = self._commHandler.onOpen(id)
        log.debug("open new connection with ID: %s " % getUnicode(self.ID))

    def on_message(self, message):
        log.debug("Message received from ID: %s\n%s " % (getUnicode(self.ID), getUnicode(message)))
        self._commHandler.onAsyncMessage(message)

    def on_close(self):
        log.debug("client closed %s" % self._commHandler.__dict__.get("ID", "None"))
        self._commHandler.onClose()

    def check_origin(self, origin):
        return True
