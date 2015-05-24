import json
import logging
import sys
import tornado
import tornado.websocket
from Asynchronous import asynchronous
from HubDecorator import HubDecorator
import inspect
from LogFunctionAction import LogFunction

__author__ = 'jgarc'

log = logging.getLogger(__name__)

class TornadoProtocolMessage:
    def __init__(self, messageStr, client):
        msgObj = json.loads(messageStr)
        self.cls = HubDecorator.HUBs_DICT[msgObj["hub"]]
        self.className = msgObj["hub"]
        self.args = msgObj["args"]
        self.args.insert(0, client)
        self.client = client
        self.functionName = msgObj["function"]
        self.method = getattr(self.cls, self.functionName)
        self.ID = msgObj.get("ID",-1)

    def __executeFunction(self):
        try:
            return True, self.method(*self.args)
        except Exception as e:
            log.exception(e)
            return False, str(e)

    def callFunction(self):
        success, replay = self.__executeFunction()
        replay = replay if  not hasattr(replay,"__dict__") else replay.__dict__
        return {
            "success": success,
            "replay": replay,
            "hub": self.className,
            "function": self.functionName,
            "ID": self.ID
        }

class MessageHandler(tornado.websocket.WebSocketHandler):
    clients = {}

    def open(self, *args):
        self.ID = int(args[0])
        log.debug("open new connection with ID: %d " % self.ID)
        self.clients[self.ID] = self

    def on_message(self, message):
        self.__async_on_message(message)

    def on_close(self):
        log.debug("client closed %s" % self.__dict__.get("ID", "None"))
        if self.ID in self.clients.keys():
            self.clients.pop(self.ID)

    def check_origin(self, origin):
        return True

    def __getattr__(self, item):
        def clientFunction(*args):
            hubName = self.__getHubName()
            message = {"function": item, "args": list(args), "hub": hubName}
            msgStr = json.dumps(message)
            log.debug("message to %s:\n%s" % (self.ID, msgStr))
            self.write_message(msgStr)

        return clientFunction

    @asynchronous()
    def __async_on_message(self, message):
        log.debug("message from %s:\n%s" % (self.ID, message))
        try:
            msg = TornadoProtocolMessage(message, self)
            replay = msg.callFunction()
            try:
                replayStr = json.dumps(replay)
            except Exception as e:
                replayStr = json.dumps(replay.__dict__)
            log.debug("message to %s:\n%s" % (self.ID, replayStr))
            self.write_message(replayStr)
        except Exception as e:
            log.exception(e)

    @staticmethod
    def __getHubName():  # todo, try to optimize checking only Hub classes
        frame = inspect.currentframe().f_back.f_back
        code = frame.f_code
        name = code.co_name
        for className, obj in frame.f_globals.items():
            try:
                func = obj.__dict__[name]
                func_code = func.func_code if sys.version_info[0] == 2 else func.__code__
                assert func_code is code
            except Exception as e:
                pass
            else:  # obj is the class that defines our method
                return className