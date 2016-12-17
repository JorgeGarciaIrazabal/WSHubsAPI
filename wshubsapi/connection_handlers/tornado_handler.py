import logging

from wshubsapi.connected_client import ConnectedClient
from wshubsapi.comm_environment import CommEnvironment
import tornado.websocket

__author__ = 'Jorge'
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class ConnectionHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        super(ConnectionHandler, self).__init__(application, request, **kwargs)
        self.comm_environment = CommEnvironment.get_instance()
        self._connected_client = ConnectedClient(self.comm_environment, self.write_message)

    def data_received(self, chunk):
        pass

    def write_message(self, message, binary=False):
        future = super(ConnectionHandler, self).write_message(message, binary)
        log.debug("message to %s:\n%s" % (self._connected_client.ID, message))
        return future

    def open(self, name=None):
        client_id = name
        id_ = self.comm_environment.on_opened(self._connected_client, client_id)
        log.debug("open new connection with ID: {} ".format(id_))

    def on_message(self, message):
        log.debug(u"Message received from ID: {}\n{} ".format(self._connected_client.ID, message))
        self.comm_environment.on_message(self._connected_client, message)

    def on_close(self):
        log.debug("client closed %s" % self._connected_client.__dict__.get("ID", "None"))
        self.comm_environment.on_closed(self._connected_client)

    def check_origin(self, origin):
        return True
