import logging

from wshubsapi.connected_client import ConnectedClient

from wshubsapi.comm_environment import CommEnvironment
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
        self._connectedClient = ConnectedClient(self.comm_environment, self.write_message)

    def data_received(self, chunk):
        pass

    def write_message(self, message, binary=False):
        future = super(ConnectionHandler, self).write_message(message, binary)
        log.debug("message to %s:\n%s" % (self._connectedClient.ID, message))
        return future

    def open(self, *args):
        try:
            client_id = int(args[0])
        except ValueError:
            client_id = None
        id_ = self.comm_environment.on_opened(self._connectedClient, client_id)
        log.debug("open new connection with ID: {} ".format(id_))

    def on_message(self, message):
        log.debug("Message received from ID: {}\n{} ".format(self._connectedClient.ID, message))
        self.comm_environment.on_async_message(self._connectedClient, message)

    def on_close(self):
        log.debug("client closed %s" % self._connectedClient.__dict__.get("ID", "None"))
        self.comm_environment.on_closed(self._connectedClient)

    def check_origin(self, origin):
        return True
