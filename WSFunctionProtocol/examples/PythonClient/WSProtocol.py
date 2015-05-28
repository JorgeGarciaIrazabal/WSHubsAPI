from __future__ import print_function
import json
import logging
import threading
from ws4py.client.threadedclient import WebSocketClient
import time
from threading import Timer

log = logging.getLogger(__name__)

__wsConnection = None
""":type WSConnection"""

class WSSimpleObject(object):
    def __setattr__(self, key, value):
        return super(WSSimpleObject, self).__setattr__(key, value)

class WSReturnObject:
    class WSCallbacks:
        def __init__(self, onSuccess=None, onError=None):
            self.onSuccess = onSuccess
            self.onError = onError

    def done(self, onSuccess, onError=None):
        pass


class WSClient(object):
    MyHubTest = WSSimpleObject()
    TestClass2 = WSSimpleObject()

class WSServer(object):
    _messageID = 0
    _messageLock = threading.RLock()

    @classmethod
    def getNextMessageID(cls):
        with cls._messageLock:
            cls._messageID += 1
            return cls._messageID
    
    class MyHubTest(object):
        
        @classmethod
        def tast(cls, a=5, b=1, c=3):
            """
            :rtype : WSReturnObject
            """
            args = list()
            args.append(a)
            args.append(b)
            args.append(c)
            id = WSServer.getNextMessageID()
            body = {"hub": cls.__name__, "function": "tast", "args": args, "ID": id}
            WSConnection._instance.send(json.dumps(body))
            return WSConnection._instance._getReturnFunction(id)
        
        @classmethod
        def test(cls, a=1, b=2):
            """
            :rtype : WSReturnObject
            """
            args = list()
            args.append(a)
            args.append(b)
            id = WSServer.getNextMessageID()
            body = {"hub": cls.__name__, "function": "tast", "args": args, "ID": id}
            WSConnection._instance.send(json.dumps(body))
            return WSConnection._instance._getReturnFunction(id)
        
    class TestClass2(object):
        
        @classmethod
        def tast(cls, a=5, b=1, c=3):
            """
            :rtype : WSReturnObject
            """
            args = list()
            args.append(a)
            args.append(b)
            args.append(c)
            id = WSServer.getNextMessageID()
            body = {"hub": cls.__name__, "function": "tast", "args": args, "ID": id}
            WSConnection._instance.send(json.dumps(body))
            return WSConnection._instance._getReturnFunction(id)
        
        @classmethod
        def test(cls, a=1, b=2):
            """
            :rtype : WSReturnObject
            """
            args = list()
            args.append(a)
            args.append(b)
            id = WSServer.getNextMessageID()
            body = {"hub": cls.__name__, "function": "tast", "args": args, "ID": id}
            WSConnection._instance.send(json.dumps(body))
            return WSConnection._instance._getReturnFunction(id)
        

class WSConnection(WebSocketClient):
    SERVER_TIMEOUT = 5.0
    _instance = None
    """:type WSConnection"""

    def __init__(self, url):
        super(WSConnection, self).__init__(url)
        self.client = WSClient()
        self.server = WSServer()
        self.__returnFunctions = dict()
        self.isOpened = False
        """:type dict of WSReturnObject.WSCallbacks"""

    @staticmethod
    def init(url, serverTimeout=5.0):
        """
        :rtype : WSConnection
        """
        WSConnection._instance = WSConnection(url)
        WSConnection.SERVER_TIMEOUT = serverTimeout
        return WSConnection._instance

    def opened(self):
        self.isOpened = True
        log.debug("Connection opened")

    def closed(self, code, reason=None):
        log.debug("Connection closed with code:\n%s\nAnd reason:\n%s"%(code,reason))

    def received_message(self, m):
        try:
            msgObj = json.loads(m.data)
            if "replay" in msgObj:
                f = self.__returnFunctions.get(msgObj["ID"], None)
                if f and msgObj["success"]:
                    f.onSuccess(msgObj["replay"])
                elif f and f.onError:
                    f.onError(msgObj["replay"])
            else:
                self.client.__getattribute__(msgObj["hub"]).__dict__[msgObj["function"]](*msgObj["args"])
        except Exception as e:
            self.onError(e)

    def _getReturnFunction(self, ID):
        """
        :rtype : WSReturnObject
        """

        def returnFunction(onSuccess, onError=None):
            callBacks = self.__returnFunctions.get(ID, WSReturnObject.WSCallbacks())

            def onSuccessWrapper(*args, **kwargs):
                onSuccess(*args, **kwargs)
                self.__returnFunctions.pop(ID, None)

            callBacks.onSuccess = onSuccessWrapper
            if onError is not None:
                def onErrorWrapper(*args, **kwargs):
                    onError(*args, **kwargs)
                    self.__returnFunctions.pop(ID, None)

                callBacks.onError = onErrorWrapper
            else:
                callBacks.onError = None
            self.__returnFunctions[ID] = callBacks
            r = Timer(self.SERVER_TIMEOUT, self.onTimeOut, (ID,))
            r.start()

        retObject = WSReturnObject()
        retObject.done = returnFunction

        # todo create timeout
        return retObject

    def onError(self, exception):
        log.exception("Error in protocol")

    def onTimeOut(self, messageId):
        f = self.__returnFunctions.pop(messageId, None)
        if f and f.onError:
            f.onError("timeOut Error")
