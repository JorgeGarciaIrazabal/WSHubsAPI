import logging
import SocketServer
import threading
from _socket import error
import socket

from wshubsapi.ConnectedClient import ConnectedClient
from wshubsapi.CommEnvironment import CommEnvironment
from wshubsapi.utils import MessageSeparator

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class SocketHandler(SocketServer.BaseRequestHandler):
    commEnvironment = None

    def __init__(self, request, client_address, server):
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
        # never enter here :O
        self.__connectedClient = None
        self.__messageSeparator = None
        """:type : MessageSeparator"""

    def setup(self):
        self.__connectedClient = None
        self.__messageSeparator = MessageSeparator()

        if SocketHandler.commEnvironment is None:
            SocketHandler.commEnvironment = CommEnvironment()
        self.__connectedClient = ConnectedClient(self.commEnvironment, self.writeMessage)
        self.commEnvironment.onOpen(self.__connectedClient)

    def writeMessage(self, message):
        self.request.sendall(message + self.__messageSeparator.separator)
        log.debug("message to %s:\n%s" % (self.__connectedClient.ID, message))

    def handle(self):
        while not self.__connectedClient.api_isClosed:
            try:
                data = self.request.recv(10240)
            except error as e:
                if e.errno == 10054:
                    self.finish()
            except:
                log.exception("error receiving data")
            else:
                for m in self.__messageSeparator.add_data(data):
                    log.debug("Message received from ID: %s\n%s " % (str(self.__connectedClient.ID), str(m)))
                    self.commEnvironment.onAsyncMessage(self.__connectedClient, m)

    def finish(self):
        log.debug("client closed %s" % self.__connectedClient.__dict__.get("ID", "None"))
        self.commEnvironment.onClosed(self.__connectedClient)


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


def createSocketServer(host, port, SocketHandlerClass=SocketHandler):
    return ThreadedTCPServer((host, port), SocketHandlerClass)


class SocketClient:
    class Message:
        def __init__(self, message):
            self.data = message

    def __init__(self, url):
        """
        :type url: str
        """
        url = url.split("//", 1)[-1]  # cleaning protocol
        url = url.split("/", 1)[0]  # cleaning extra parameters
        h, p = url.split(":")
        self.host, self.port = h, int(p)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__messageSeparator = MessageSeparator()

    def connect(self):
        self.socket.connect((self.host, self.port))
        server_thread = threading.Thread(target=self.receiveMessageThread)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()

    def send(self, message):
        # this will crash if not ascii
        self.socket.sendall(message + self.__messageSeparator.separator)

    def receiveMessageThread(self):
        while True:
            try:
                data = self.socket.recv(1024)
            except:
                log.exception("Error receiving message")
                break
            if data != "":
                for m in self.__messageSeparator.add_data(data):
                    self.received_message(self.Message(m))

    def received_message(self, message):
        raise NotImplemented
