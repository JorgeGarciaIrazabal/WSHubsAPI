import socket
import logging

from wshubsapi.ConnectionHandlers.API_SocketServer import API_SocketServer

from wshubsapi.CommEnvironment import CommEnvironment

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class SocketHandler(API_SocketServer):
    commEnvironment = None
    API_SEP = "*API_SEP*"

    def __init__(self, IP=socket.gethostbyname(socket.gethostname()), port=9999, *args, **kwargs):
        super(SocketHandler, self).__init__(IP, port, *args, **kwargs)
        if SocketHandler.commEnvironment is None:
            SocketHandler.commEnvironment = CommEnvironment()

        self.clientConnectedClientHashMap = dict()
        """ :type : dict[SocketServer.ConnectedClient,wshubsapi.ConnectedClient.ConnectedClient]"""

    def onClientConnected(self, client):
        connectedClient = self.commEnvironment.constructConnectedClient(
            lambda m: client.socket.sendall(m + self.API_SEP))
        connectedClient.onOpen()
        self.clientConnectedClientHashMap[client] = connectedClient

        def onClose():
            log.debug("client closed %s" % connectedClient.__dict__.get("ID", "None"))
            connectedClient.onClosed()
            self.clientConnectedClientHashMap.pop(client, None)

        client.onClose = onClose
        log.debug("open new connection with ID: {} ".format(connectedClient.ID))

    def onMessageReceived(self, client, message):
        connectedClient = self.clientConnectedClientHashMap[client]
        messages = message.split("}{")
        if len(messages) == 0:
            log.debug("Message received from ID: %s\n%s " % (str(connectedClient.ID), str(message)))
            return connectedClient.onAsyncMessage(message)
        for i, m in enumerate(messages):
            if i == 0:
                m += "}"
            elif i == len(messages) - 1:
                m = "{" + m
            else:
                m = "{" + m + "}"
            log.debug("Message received from ID: %s\n%s " % (str(connectedClient.ID), str(m)))
            connectedClient.onAsyncMessage(m)
