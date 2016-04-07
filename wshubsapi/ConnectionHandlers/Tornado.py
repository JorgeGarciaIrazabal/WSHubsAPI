import logging

from wshubsapi.ConnectedClient import ConnectedClient

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
        self._connectedClient = ConnectedClient(self.commEnvironment, self.writeMessage)

    def data_received(self, chunk):
        pass

    def writeMessage(self, message):
        self.write_message(message)
        log.debug("message to %s:\n%s" % (self._connectedClient.ID, message))

    def open(self, *args):
        try:
            clientId = int(args[0])
        except:
            clientId = None
        ID = self.commEnvironment.on_opened(self._connectedClient, clientId)
        log.debug("open new connection with ID: {} ".format(ID))

    def on_message(self, message):
        log.debug("Message received from ID: {}\n{} ".format(self._connectedClient.ID, message))
        self.commEnvironment.on_async_message(self._connectedClient, message)

    def on_close(self):
        log.debug("client closed %s" % self._connectedClient.__dict__.get("ID", "None"))
        self.commEnvironment.on_closed(self._connectedClient)

    def check_origin(self, origin):
        return True
