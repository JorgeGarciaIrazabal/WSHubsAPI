import json
import logging
import threading
from datetime import datetime, timedelta
import time

try:
    from Queue import Queue
except:
    from queue import Queue
from jsonpickle.pickler import Pickler
from concurrent.futures import Future

from wshubsapi.ConnectedClientsHolder import ConnectedClientsHolder
from wshubsapi.FunctionMessage import FunctionMessage
from wshubsapi.utils import setSerializerDateTimeHandler, serializeMessage
from wshubsapi.MessagesReceivedQueue import MessagesReceivedQueue
# do not remove this line (hubs inspector needs to find it)
from wshubsapi import UtilsAPIHub, Asynchronous

log = logging.getLogger(__name__)
__author__ = 'Jorge Garcia Irazabal'

_DEFAULT_PICKER = Pickler(max_depth=5, max_iter=80, make_refs=False)

setSerializerDateTimeHandler()  # todo move this


class HubsApiException(Exception):
    pass


class CommEnvironment(object):
    def __init__(self, maxWorkers=MessagesReceivedQueue.DEFAULT_MAX_WORKERS,
                 unprovidedIdTemplate="UNPROVIDED__{}", pickler=_DEFAULT_PICKER,
                 clientFunctionTimeout=5):
        self.lock = threading.Lock()
        self.availableUnprovidedIds = list()
        self.unprovidedIdTemplate = unprovidedIdTemplate
        self.lastProvidedId = 0
        self.wsMessageReceivedQueue = MessagesReceivedQueue(self, maxWorkers)
        self.wsMessageReceivedQueue.startThreads()
        self.allConnectedClients = ConnectedClientsHolder.allConnectedClientsDict
        self.pickler = pickler
        self.clientFunctionTimeout = clientFunctionTimeout
        self.__lastClientMessageID = 0
        self.__newClientMessageIDLock = threading.Lock()
        self.__futuresBuffer = {}
        self.__checkFutures()
        """:type : dict[int, list[Future, datetime]]"""

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

    def onMessage(self, client, messageStr):
        try:
            messageStr = messageStr if isinstance(messageStr, str) else messageStr.decode("utf-8")
            msgObj = json.loads(messageStr)
            if "replay" not in msgObj:
                self.__onReplay(client, messageStr, msgObj)
            else:
                self.__onReplayed(msgObj)


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

    def getNewClientsFuture(self):
        with self.__newClientMessageIDLock:
            self.__lastClientMessageID += 1
            ID = self.__lastClientMessageID
            self.__futuresBuffer[ID] = [Future(), datetime.now()]
        return self.__futuresBuffer[ID][0], ID

    @Asynchronous.asynchronous()
    def __checkFutures(self):
        while True:
            for ID, [f, d] in self.__futuresBuffer.items():
                if datetime.now() - d > timedelta(seconds=self.clientFunctionTimeout):
                    self.__onTimeOut(ID)
            time.sleep(0.1)

    def __onTimeOut(self, ID):
        with self.__newClientMessageIDLock:
            if ID in self.__futuresBuffer:
                future = self.__futuresBuffer.pop(ID)[0]
                future.set_exception(HubsApiException("Timeout exception"))

    def __onReplay(self, client, messageStr, msgObj):
        hubFunction = FunctionMessage(msgObj, client)
        replay = hubFunction.callFunction()
        if replay is not None:
            self.replay(client, replay, messageStr)

    def __onReplayed(self, msgObj):
        future = self.__futuresBuffer.pop(msgObj["ID"], [None])[0]
        if future is not None:
            if msgObj["success"]:
                future.set_result(msgObj["replay"])
            else:
                future.set_exception(Exception(msgObj["replay"]))
