import logging

from wshubsapi.ConnectedClient import ConnectedClient

from wshubsapi.CommEnvironment import CommEnvironment
import tornado.websocket

__author__ = 'Jorge'
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class ConnectionHandler(tornado.websocket.WebSocketHandler):
    comm_environment = None

    def __init__(self, application, request, **kwargs):
        super(ConnectionHandler, self).__init__(application, request, **kwargs)
        if ConnectionHandler.comm_environment is None:
            ConnectionHandler.comm_environment = CommEnvironment()
        self._connectedClient = ConnectedClient(self.comm_environment, self.writeMessage)

    def data_received(self, chunk):
        pass

    def write_message(self, message, binary=False):
        future = super(ConnectionHandler, self).write_message(message, binary)
        log.debug("message to %s:\n%s" % (self._connectedClient.ID, message))
        return future

    def open(self, *args):
        try:
            clientId = int(args[0])
        except:
            clientId = None
        ID = self.comm_environment.on_opened(self._connectedClient, clientId)
        log.debug("open new connection with ID: {} ".format(ID))

    def on_message(self, message):
        log.debug("Message received from ID: {}\n{} ".format(self._connectedClient.ID, message))
        self.comm_environment.on_async_message(self._connectedClient, message)

    def on_close(self):
        log.debug("client closed %s" % self._connectedClient.__dict__.get("ID", "None"))
        self.comm_environment.on_closed(self._connectedClient)

    def check_origin(self, origin):
        return True
