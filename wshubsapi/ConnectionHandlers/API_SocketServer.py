# -*- coding: utf8 -*-
import socket
import threading


class ConnectedClient:
    def __init__(self, socketObj, address):
        self.socket = socketObj
        self.address = address
        self.ID = None

    def onClose(self):
        pass

    def __str__(self):
        return "Client in-> Socket: %s, Address: %s" % (self.socket, self.address)


class API_SocketServer(socket.socket):
    SOCKET_BUFFER_SIZE = 1024 * 10

    def __init__(self, IP="127.0.0.1", port=9999, *args, **kwargs):
        super(API_SocketServer, self).__init__(*args, **kwargs)
        self.IP = IP
        self.port = port
        self.bind((IP, port))
        self.listen(1)
        self.clients = []
        self.keepAlive = True
        self.acceptThread = threading.Thread(target=self._acceptConnection)
        self.acceptThread.setDaemon(True)
        self.acceptThread.start()
        self.readMsgThreads = []  # threads to read msg
        self.packetBuffer = {}

    # one thread
    def _acceptConnection(self):
        threading.current_thread().name = "RServer accept thread"
        print "accepting connection"
        while self.keepAlive:
            sc, addr = self.accept()
            self.clients.append(ConnectedClient(socketObj=sc, address=addr))
            client = self.clients[-1]
            thread = threading.Thread(target=self._readClientMessage, args=(client,))
            thread.setDaemon(True)
            thread.start()
            self.readMsgThreads.append(thread)
            self.onClientConnected(client)

    # one thread for each client
    def _readClientMessage(self, client):
        threading.current_thread().name += " RServer Client reader"
        while self.keepAlive:
            try:
                message = client.socket.recv(self.SOCKET_BUFFER_SIZE)
                if message == "":
                    self.onClosed(client)
                    break
                self.onMessageReceived(client, message)
            except (IOError, socket.error) as e:
                self.onError(client, e)
                client.socket.close()
                self.clients.remove(client)
                self.onClosed(client)
                break
            except Exception as e:
                self.onError(client, e)

    def onClientConnected(self, client):
        """
        :type client: ConnectedClient
        """
        pass

    def onMessageReceived(self, client, message):
        """
        :type message: str
        :type client: ConnectedClient
        """
        pass

    def onError(self, client, exception):
        """
        :type client: ConnectedClient
        """
        pass

    def onClosed(self, client):
        """
        :type client: ConnectedClient
        """
        client.onClose()
        pass

    def _closeClientSockets(self):
        for client in self.clients:
            client.socket.shutdown(socket.SHUT_RDWR)
            client.socket.close()

    def stopCommunication(self):
        self.keepAlive = False
        self._closeClientSockets()
        for thread in self.readMsgThreads:
            thread.join()
            # self.shutdown(socket.SHUT_RDWR)
            # self.close()

    def __str__(self):
        return "RServer in-> IP: %s, PORT: %d" % (self.IP, self.port)
