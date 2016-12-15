import logging
from ws4py.websocket import WebSocket
from wshubsapi.connected_client import ConnectedClient

from wshubsapi.comm_environment import CommEnvironment

__author__ = 'Jorge'
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class ConnectionHandler(WebSocket):
    def __init__(self, sock, protocols=None, extensions=None, environ=None, heartbeat_freq=None):
        super(ConnectionHandler, self).__init__(sock, protocols, extensions, environ, heartbeat_freq)
        self.comm_environment = CommEnvironment.get_instance()
        self._connected_client = ConnectedClient(self.comm_environment, self.write_message)

    def write_message(self, message):
        self.send(message)
        log.debug("message to %s:\n%s" % (self._connected_client.ID, message))

    def opened(self):
        client_id = None
        id_ = self.comm_environment.on_opened(self._connected_client, client_id)
        log.debug("open new connection with ID: {} ".format(id_))

    def received_message(self, message):
        log.debug("Message received from ID: %s\n%s " % (str(self._connected_client.ID), str(message)))
        self.comm_environment.on_message(self._connected_client, message.data)

    def closed(self, code, reason=None):
        log.debug("client closed %s" % self._connected_client.__dict__.get("ID", "None"))
        self.comm_environment.on_closed(self._connected_client)
