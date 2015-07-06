from inspect import isclass
import json
import logging
import sys
import inspect
import threading

from WSHubsAPI.ValidateStrings import getUnicode
from WSHubsAPI.utils import classProperty, WSThreadsQueue, serializeObject

log = logging.getLogger(__name__)
__author__ = 'Jorge Garcia Irazabal'

class CommHandler(object):
    __LAST_UNPROVIDED_ID = 0
    __UNPROVIDED_TEMPLATE = "__%d"
    _connections = {}
    __AVAILABLE_UNPROVIDED_IDS = []
    threadsPool = WSThreadsQueue(50)  # todo: make dynamic queue size
    __lock = threading.Lock()

    def __init__(self, client=None):
        self.ID = None
        self.client = client

    @classmethod
    def getUnprovidedID(cls):
        if len(cls.__AVAILABLE_UNPROVIDED_IDS) > 0:
            return cls.__AVAILABLE_UNPROVIDED_IDS.pop(0)
        while cls.__UNPROVIDED_TEMPLATE % cls.__LAST_UNPROVIDED_ID in cls._connections:
            cls.__LAST_UNPROVIDED_ID += 1
        return cls.__UNPROVIDED_TEMPLATE % cls.__LAST_UNPROVIDED_ID

    def onOpen(self, ID=None):
        with self.__lock:
            if ID is None or ID in self._connections:
                self.ID = self.getUnprovidedID()
            else:
                self.ID = ID
            self._connections[self.ID] = self
            return self.ID

    def onMessage(self, message):
        try:
            msg = FunctionMessage(message, self)
            replay = msg.callFunction()
            self.onReplay(replay, msg)
        except Exception as e:
            self.onError(e)

    def onAsyncMessage(self, message):
        self.threadsPool.put((message, self))

    def onClose(self):
        if self.ID in self._connections.keys():
            self._connections.pop(self.ID)
            if isinstance(self.ID, str) and self.ID.startswith("__"):
                self.__AVAILABLE_UNPROVIDED_IDS.append(self.ID)

    def onError(self, exception):
        log.exception("Error parsing message")

    def onReplay(self, replay, message):
        try:
            replayStr = json.dumps(replay)
        except:
            replayStr = json.dumps(replay.__dict__)

        self.writeMessage(replayStr)

    def __getattr__(self, item):
        if item.startswith("__") and item.endswith("__"):
            return

        def connectionFunction(*args):
            hubName = self.__getHubName()
            message = {"function": item, "args": serializeObject(list(args)), "hub": hubName}
            msgStr = json.dumps(message)
            self.writeMessage(msgStr)

        return connectionFunction

    def writeMessage(self, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def __getHubName():  # todo, try to optimize checking only Hub classes
        frame = inspect.currentframe()
        while frame.f_back is not None:
            frame = frame.f_back
            code = frame.f_code
            name = code.co_name
            hubs = filter(lambda x: isclass(x[1]) and issubclass(x[1], Hub), frame.f_globals.items())
            for hubName, hub in hubs:
                try:
                    func = hub.__dict__[name]
                    func_code = func.func_code if sys.version_info[0] == 2 else func.__code__
                    assert func_code is code
                except Exception as e:
                    pass
                else:  # obj is the class that defines our method
                    return hub.__HubName__

    @classProperty
    def connections(cls):
        return cls._connections

class ConnectionGroup(list):
    def __init__(self, connections):
        """
        :type connections: list of CommHandler
        """
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
        replay = serializeObject(replay)
        return {
            "success": success,
            "replay": replay,
            "hub": self.className,
            "function": self.functionName,
            "ID": self.ID
        }

from WSHubsAPI.Hub import Hub
