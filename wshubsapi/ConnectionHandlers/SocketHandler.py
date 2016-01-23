import socket
import logging

from wshubsapi.ConnectionHandlers.SocketServer import SocketServer

from wshubsapi.CommEnvironment import CommEnvironment

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class SocketHandler(SocketServer):
    commEnvironment = None

    def __init__(self, IP=socket.gethostbyname(socket.gethostname()), port=9999, *args, **kwargs):
        super(SocketHandler, self).__init__(IP, port, *args, **kwargs)
        if self.commEnvironment is None:
            self.commEnvironment = CommEnvironment()

        self.clientConnectedClientHashMap = dict()
        """ :type : dict[SocketServer.ConnectedClient,wshubsapi.ConnectedClient.ConnectedClient]"""

    def onClientConnected(self, client):
        connectedClient = self.commEnvironment.constructConnectedClient(client.socket.sendall)
        self.clientConnectedClientHashMap[client] = connectedClient

        def onClose():
            log.debug("client closed %s" % connectedClient.__dict__.get("ID", "None"))
            connectedClient.onClosed()
            self.clientConnectedClientHashMap.pop(client, None)

        client.onClose = onClose

    def onMessageReceived(self, client, message):
        connectedClient = self.clientConnectedClientHashMap[client]
        log.debug("Message received from ID: %s\n%s " % (str(connectedClient.ID), str(message)))
        connectedClient.onAsyncMessage(message)
