from inspect import isclass
import json
import logging
import sys
import inspect
import threading
from datetime import datetime
import jsonpickle
from jsonpickle.pickler import Pickler

from wshubsapi.ValidateStrings import getUnicode
from wshubsapi.utils import WSMessagesReceivedQueue, setSerializerDateTimeHandler

log = logging.getLogger(__name__)
__author__ = 'Jorge Garcia Irazabal'

_DEFAULT_PICKER = Pickler(max_depth=5, max_iter=80, make_refs=False)

setSerializerDateTimeHandler()


class CommProtocol(object):
    def __init__(self, messageReceivedThreadPoolSize=20, unprovidedIdTemplate="UNPROVIDED__%d"):
        self.lock = threading.Lock()
        self.availableUnprovidedIds = list()
        self.connections = dict()
        self.unprovidedIdTemplate = unprovidedIdTemplate
        self.lastProvidedId = 0
        self.messageReceivedThreadPoolSize = messageReceivedThreadPoolSize
        self.wsMessageReceivedQueue = WSMessagesReceivedQueue(
            messageReceivedThreadPoolSize)  # todo: make dynamic queue size
        self.wsMessageReceivedQueue.startThreads()

    def constructCommHandler(self, client=None, serializationPickler=_DEFAULT_PICKER):
        return CommHandler(client, serializationPickler, self)

    def getUnprovidedID(self):
        if len(self.availableUnprovidedIds) > 0:
            return self.availableUnprovidedIds.pop(0)
        while self.unprovidedIdTemplate % self.lastProvidedId in self.connections:
            self.lastProvidedId += 1
        return self.unprovidedIdTemplate % self.lastProvidedId


class CommHandler(object):
    def __init__(self, client=None, serializationPickler=_DEFAULT_PICKER, commProtocol=None):
        """
        :type commProtocol: CommProtocol
        """
        self.ID = None
        self.client = client
        self.pickler = serializationPickler
        self.__commProtocol = commProtocol

    def onOpen(self, ID=None):
        with self.__commProtocol.lock:
            if ID is None or ID in self.__commProtocol.connections:
                self.ID = self.__commProtocol.getUnprovidedID()
            else:
                self.ID = ID
            self.__commProtocol.connections[self.ID] = self
            return self.ID

    def onMessage(self, message):
        try:
            msg = FunctionMessage(message, self)
            replay = msg.callFunction()
            self.onReplay(self.serializeMessage(replay), msg)
        except Exception as e:
            self.onError(e)

    def onAsyncMessage(self, message):
        self.__commProtocol.wsMessageReceivedQueue.put((message, self))

    def onClose(self):
        if self.ID in self.connections.keys():
            self.__commProtocol.connections.pop(self.ID)
            if isinstance(self.ID, str) and self.ID.startswith(
                    "UNPROVIDED__"):  # todo, need a regex to check if is unprovided
                self.__commProtocol.availableUnprovidedIds.append(self.ID)

    def onError(self, exception):
        log.exception("Error parsing message")

    def onReplay(self, replay, message):
        """
        :param replay: serialized object to be sent as a replay of a message received
        :param message: Message received (provided for overridden functions)
        """
        self.writeMessage(replay)

    def __getattr__(self, item):
        if item.startswith("__") and item.endswith("__"):
            return

        def connectionFunction(*args):
            hubName = self.__getHubName()
            message = {"function": item, "args": list(args), "hub": hubName}
            msgStr = self.serializeMessage(message)
            self.writeMessage(msgStr)

        return connectionFunction

    def writeMessage(self, *args, **kwargs):
        raise NotImplementedError

    def serializeMessage(self, message):
        return jsonpickle.encode(self.pickler.flatten(message))

    @staticmethod
    def __getHubName():
        frame = inspect.currentframe()
        while frame.f_back is not None:
            frame = frame.f_back
            code = frame.f_code
            name = code.co_name
            hubs = filter(lambda x: isclass(x[1]) and issubclass(x[1], Hub), frame.f_globals.items())
            for hubName, hub in hubs:
                try:
                    func = hub.__dict__[name]
                    if isinstance(func,(classmethod, staticmethod)): func = func.__func__
                    func_code = func.func_code if sys.version_info[0] == 2 else func.__code__
                    assert func_code is code
                except Exception as e:
                    pass
                else:  # obj is the class that defines our method
                    return hub.__HubName__

    @property
    def connections(self):
        return self.__commProtocol.connections


class ConnectionGroup(list):
    def __init__(self, connections):
        """
        :type connections: list of CommHandler
        """
        super(ConnectionGroup, self).__init__()
        for c in connections:
            self.append(c)

    def append(self, p_object):
        if isinstance(p_object, CommHandler):
            super(ConnectionGroup, self).append(p_object)
        else:
            raise TypeError()

    def __getattr__(self, item):
        functions = []
        for c in self:
            functions.append(c.__getattr__(item))

        def connectionFunctions(*args):
            for f in functions:
                f(*args)

        return connectionFunctions

    def __getitem__(self, item):
        """
        :rtype : CommHandler
        """
        return super(ConnectionGroup, self).__getitem__(item)


class FunctionMessage:
    def __init__(self, messageStr, connection):
        msgObj = json.loads(messageStr)
        self.cls = Hub.HUBs_DICT[msgObj["hub"]]
        self.className = msgObj["hub"]
        self.args = msgObj["args"]
        self.connection = connection

        self.functionName = msgObj["function"]
        self.method = getattr(self.cls, self.functionName)
        self.ID = msgObj.get("ID", -1)

    def __executeFunction(self):
        try:
            return True, self.method(*self.args)
        except Exception as e:
            log.exception("Error calling hub function")
            return False, getUnicode(e)

    def callFunction(self):
        success, replay = self.__executeFunction()
        return {
            "success": success,
            "replay": replay,
            "hub": self.className,
            "function": self.functionName,
            "ID": self.ID,
            "serverDateTime": datetime.now()
        }


from wshubsapi.Hub import Hub
