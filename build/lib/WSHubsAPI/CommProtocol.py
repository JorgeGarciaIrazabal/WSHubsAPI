import json
import logging
import sys
import inspect
import threading

from HubDecorator import HubDecorator
from utils import classproperty, WSThreadsQueue, serializeObject

log = logging.getLogger(__name__)
__author__ = 'Jorge Garcia Irazabal'

class CommHandler(object):
    __LAST_UNPROVIDED_ID = 0
    __UNPROVIDED_TEMPLATE = "__%d"
    _connections = {}
    __AVAILABLE_UNPROVIDED_IDS = []
    threadsPool = WSThreadsQueue(50) #todo: make dynamic queue size
    __lock = threading.Lock()
    def __init__(self, client=None):
        self.ID = None
        self.client = client

    @classmethod
    def getUnprovidedID(cls):
        if len(cls.__AVAILABLE_UNPROVIDED_IDS)>0:
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
            self.onReplay(replay,msg)
        except Exception as e:
            self.onError(e)

    def onAsyncMessage(self, message):
        self.threadsPool.put((message,self))

    def onClose(self):
        if self.ID in self._connections.keys():
            self._connections.pop(self.ID)
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
            message = {"function": item, "args": list(args), "hub": hubName}
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
            hubs = filter(lambda x: HubDecorator.isHub(x[1]), frame.f_globals.items())
            for hubName, hub in hubs:
                try:
                    func = hub.__dict__[name]
                    func_code = func.func_code if sys.version_info[0] == 2 else func.__code__
                    assert func_code is code
                except Exception as e:
                    pass
                else:  # obj is the class that defines our method
                    return hub.__HubName__

    @classproperty
    def allClients(cls):
        return ConnectionGroup(cls._connections.values())

    @property
    def otherClients(self):
        return ConnectionGroup(filter(lambda x: x.ID != self.ID, self._connections.values()))

    def getClients(self, function):
        return ConnectionGroup(filter(function, self._connections.values()))

class ConnectionGroup:
    def __init__(self, connections):
        """
        :type connections: list of CommHandler
        """
        self.__connections = connections

    def __getattr__(self, item):
        functions = []
        for c in self.__connections:
            functions.append(c.__getattr__(item))

        def connectionFunctions(*args):
            for f in functions:
                f(*args)

        return connectionFunctions

    def __len__(self):
        return len(self.__connections)

class FunctionMessage:
    def __init__(self, messageStr, connection):
        msgObj = json.loads(messageStr)
        self.cls = HubDecorator.HUBs_DICT[msgObj["hub"]]
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
            return False, str(e)

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



