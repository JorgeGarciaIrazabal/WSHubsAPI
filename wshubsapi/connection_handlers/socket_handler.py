import logging
import socketserver
import threading
from _socket import error
import socket

from wshubsapi.connected_client import ConnectedClient
from wshubsapi.comm_environment import CommEnvironment
from wshubsapi.message_separator import MessageSeparator

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class SocketHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)
        # never enter here :O
        self.comm_environment = None
        """:type : CommEnvironment"""
        self.__connected_client = None
        self.__message_separator = None
        """:type : MessageSeparator"""

    def setup(self):
        self.__connected_client = None
        self.__message_separator = MessageSeparator()
        self.comm_environment = CommEnvironment.get_instance()
        self.__connected_client = ConnectedClient(self.comm_environment, self.write_message)
        self.comm_environment.on_opened(self.__connected_client)

    def write_message(self, message):
        self.request.sendall(message + self.__message_separator.separator)
        log.debug("message to %s:\n%s" % (self.__connected_client.ID, message))

    def handle(self):
        while not self.__connected_client.api_is_closed:
            try:
                data = self.request.recv(10240)
            except error as e:
                if e.errno == 10054:
                    self.finish()
            except:
                log.exception("error receiving data")
            else:
                for m in self.__message_separator.add_data(data):
                    log.debug("Message received from ID: %s\n%s " % (str(self.__connected_client.ID), str(m)))
                    self.comm_environment.on_message(self.__connected_client, m)

    def finish(self):
        log.debug("client closed %s" % self.__connected_client.__dict__.get("ID", "None"))
        self.comm_environment.on_closed(self.__connected_client)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def create_socket_server(host, port, socket_handler_class=SocketHandler):
    return ThreadedTCPServer((host, port), socket_handler_class)


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
        self.__message_separator = MessageSeparator()

    def connect(self):
        self.socket.connect((self.host, self.port))
        server_thread = threading.Thread(target=self.receive_message_thread)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()

    def send(self, message):
        # this will crash if not ascii
        self.socket.sendall(message + self.__message_separator.separator)

    def receive_message_thread(self):
        while True:
            try:
                data = self.socket.recv(1024)
            except:
                log.exception("Error receiving message")
                raise
            if data != "":
                for m in self.__message_separator.add_data(data):
                    self.received_message(self.Message(m))

    def received_message(self, message):
        raise NotImplemented
