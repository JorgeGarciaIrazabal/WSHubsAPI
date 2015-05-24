import json
import logging
import sys
import inspect

import tornado
import tornado.websocket

from HubDecorator import HubDecorator

__author__ = 'jgarc'

log = logging.getLogger(__name__)

class FunctionMessage:
    def __init__(self, messageStr, client):
        msgObj = json.loads(messageStr)
        self.cls = HubDecorator.HUBs_DICT[msgObj["hub"]]
        self.className = msgObj["hub"]
        self.args = msgObj["args"]
        self.args.insert(0, client)
        self.client = client

        self.functionName = msgObj["function"]
        self.method = getattr(self.cls, self.functionName)
        self.ID = msgObj.get("ID", -1)

    def __executeFunction(self):
        try:
            return True, self.method(*self.args)
        except Exception as e:
            log.exception(e)
            return False, str(e)

    def callFunction(self):
        success, replay = self.__executeFunction()
        replay = replay if not hasattr(replay, "__dict__") else replay.__dict__
        return {
            "success": success,
            "replay": replay,
            "hub": self.className,
            "function": self.functionName,
            "ID": self.ID
        }

class CommHandler:
    __LAST_UNPROVIDED_ID = 0
    __UNPROVIDED_TEMPLATE = "__%d"
    _connections = {}

    def __init__(self, client):
        self.ID = None
        self.client = client

    @classmethod
    def getUnprovidedID(cls):
        while cls.__UNPROVIDED_TEMPLATE % cls.__LAST_UNPROVIDED_ID in cls._connections:
            cls.__LAST_UNPROVIDED_ID += 1
        return cls.__UNPROVIDED_TEMPLATE % cls.__LAST_UNPROVIDED_ID

    def onOpen(self, ID=None):
        if ID is None or ID in self._connections:
            self.ID = self.getUnprovidedID()
        else: self.ID = ID
        self._connections[self.ID] = self
        return ID

    def onMessage(self, message):
        try:
            msg = FunctionMessage(message, self)
            replay = msg.callFunction()
            try:
                replayStr = json.dumps(replay)
            except Exception as e:
                replayStr = json.dumps(replay.__dict__)
            self.writeMessage(replayStr)
        except Exception as e:
            log.exception(e)

    def onClose(self):
        if self.ID in self._connections.keys():
            self._connections.pop(self.ID)

    def __getattr__(self, item):
        def clientFunction(*args):
            hubName = self.__getHubName()
            message = {"function": item, "args": list(args), "hub": hubName}
            msgStr = json.dumps(message)
            self.writeMessage(msgStr)

        return clientFunction

    def writeMessage(self, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def __getHubName():  # todo, try to optimize checking only Hub classes
        frame = inspect.currentframe().f_back
        while frame.f_back is not None:
            frame = frame.f_back
            code = frame.f_code
            name = code.co_name
            hubs = filter(lambda x: HubDecorator.isHub(x[1]),frame.f_globals.items())
            for hubName, hub in hubs:
                try:
                    func = hub.__dict__[name]
                    func_code = func.func_code if sys.version_info[0] == 2 else func.__code__
                    assert func_code is code
                except Exception as e:
                    pass
                else:  # obj is the class that defines our method
                    return hubName
    @classmethod
    def allClients(cls):
        return cls._connections.values()

    def OtherClients(self):
        return filter(lambda x: x.ID != self.ID, self._connections.values())

class ConnectionGroups:
    def __init__(self, connections):
        self.connections = connections

    def __getattr__(self, item):
        for c in self.connections:
            c

class ClientHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self._commHandler = CommHandler(self)
        self._commHandler.writeMessage = self.writeMessage
        self.ID = None

    def writeMessage(self, message):
        log.debug("message to %s:\n%s" % (self._commHandler.ID, message))
        self.write_message(message)

    def open(self, *args):
        log.debug("open new connection with ID: %d " % int(args[0]))
        self.ID = self._commHandler.onOpen(int(args[0]))

    def on_message(self, message):
        log.debug("Message received from ID: %s\n%s " % (str(self.ID), str(message)))
        self._commHandler.onMessage(message)

    def on_close(self):
        log.debug("client closed %s" % self._commHandler.__dict__.get("ID", "None"))
        self._commHandler.onClose()

    def check_origin(self, origin):
        return True
