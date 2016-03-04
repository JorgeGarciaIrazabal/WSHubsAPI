import logging
import threading
from jsonpickle.pickler import Pickler
from wshubsapi.ConnectedClient import ConnectedClient
from wshubsapi.ConnectedClientsHolder import ConnectedClientsHolder
from wshubsapi.FunctionMessage import FunctionMessage
from wshubsapi.utils import WSMessagesReceivedQueue, setSerializerDateTimeHandler, serializeMessage
#do not remove this line (hubs inspector needs to find it)
from wshubsapi import UtilsAPIHub


log = logging.getLogger(__name__)
__author__ = 'Jorge Garcia Irazabal'

_DEFAULT_PICKER = Pickler(max_depth=5, max_iter=80, make_refs=False)

setSerializerDateTimeHandler()  # todo move this


class CommEnvironment(object):
    def __init__(self, maxWorkers=WSMessagesReceivedQueue.DEFAULT_MAX_WORKERS,
                 unprovidedIdTemplate="UNPROVIDED__{}", pickler=_DEFAULT_PICKER):
        self.lock = threading.Lock()
        self.availableUnprovidedIds = list()
        self.unprovidedIdTemplate = unprovidedIdTemplate
        self.lastProvidedId = 0
        self.wsMessageReceivedQueue = WSMessagesReceivedQueue(self, maxWorkers)
        self.wsMessageReceivedQueue.startThreads()
        self.allConnectedClients = ConnectedClientsHolder.allConnectedClientsDict
        self.pickler = pickler
        self.__lastClientMessageID = 0
        self.__newClientMessageIDLock = threading.Lock()

    def getUnprovidedID(self):
        if len(self.availableUnprovidedIds) > 0:
            return self.availableUnprovidedIds.pop(0)
        while self.unprovidedIdTemplate.format(self.lastProvidedId) in self.allConnectedClients:
            self.lastProvidedId += 1
        return self.unprovidedIdTemplate.format(self.lastProvidedId)

    def onOpen(self, client, ID=None):
        with self.lock:
            if ID is None or ID in self.allConnectedClients:
                client.ID = self.getUnprovidedID()
            else:
                client.ID = ID
            ConnectedClientsHolder.appendClient(client)
            return client.ID

    def onMessage(self, client, message):
        try:
            msg = FunctionMessage(message, client)
            replay = msg.callFunction()
            if replay is not None:
                self.replay(client, replay, message)
        except Exception as e:
            self.onError(client, e)

    def onAsyncMessage(self, client, message):
        self.wsMessageReceivedQueue.put((message, client))

    def onClosed(self, client):
        """:type client: wshubsapi.ConnectedClient.ConnectedClient"""
        ConnectedClientsHolder.popClient(client.ID)
        client.api_isClosed = True

    def onError(self, client, exception):
        log.exception("Error parsing message")

    def replay(self, client, replay, originMessage):
        """
        :type client: wshubsapi.ConnectedClient.ConnectedClient
        :param replay: serialized object to be sent as a replay of a message received
        :param originMessage: Message received (provided for overridden functions)
        """
        client.api_writeMessage(serializeMessage(self.pickler, replay))

    def getNewMessageID(self):
        with self.__newClientMessageIDLock:
            self.__lastClientMessageID += 1
            return self.__lastClientMessageID
