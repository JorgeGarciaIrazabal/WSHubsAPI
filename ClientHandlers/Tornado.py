import logging
from CommProtocol import CommHandler
import tornado.websocket
__author__ = 'Jorge'
log = logging.getLogger(__name__)

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
        log.debug("open new connection with ID: %d " % int(args[0]))
        self.ID = self._commHandler.onOpen(int(args[0]))

    def on_message(self, message):
        log.debug("Message received from ID: %s\n%s " % (str(self.ID), str(message)))
        self._commHandler.onMessage(message)

    def on_close(self):
        log.debug("client closed %s" % self._commHandler.__dict__.get("ID", "None"))
        self._commHandler.onClose()

    def check_origin(self, origin):
        return True
