import json
import logging
import threading
from ws4py.client.threadedclient import WebSocketClient
from threading import Timer
from datetime import datetime
log = logging.getLogger(__name__)

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

class GenericServer(object):
    __messageID = 0
    __messageLock = threading.RLock()

    def __init__(self, wsClient, hubName):
        """
        :type wsClient: WSHubsAPIClient
        """
        self.wsClient = wsClient
        self.hubName = hubName

    @classmethod
    def _getNextMessageID(cls):
        with cls.__messageLock:
            cls.__messageID += 1
            return cls.__messageID

    @classmethod
    def _serializeObject(cls, obj2ser):
        obj = obj2ser if not hasattr(obj2ser, "__dict__") else obj2ser.__dict__
        if isinstance(obj,dict):
            sObj = {}
            for key, value in obj.items():
                if isinstance(value,datetime):
                    sObj[key] = value.strftime('%Y/%m/%d %H:%M:%S %f')
                else:
                    try:
                        if not key.startswith("_") and id(value) != id(obj2ser):
                            sValue = cls._serializeObject(value)
                            json.dumps(cls._serializeObject(sValue))
                            sObj[key] = sValue
                    except TypeError:
                        pass
        elif isinstance(obj,(list,tuple,set)):
            sObj = []
            for value in obj:
                try:
                    sValue = cls._serializeObject(value)
                    json.dumps(sValue)
                    sObj.append(sValue)
                except TypeError:
                    pass
        else:
            sObj = obj
        return sObj


class WSHubsAPIClient(WebSocketClient):
    def __init__(self, api, url, serverTimeout):
        super(WSHubsAPIClient, self).__init__(url)
        self.__returnFunctions = dict()
        self.isOpened = False
        self.serverTimeout = serverTimeout
        self.api = api

    def opened(self):
        self.isOpened = True
        log.debug("Connection opened")

    def closed(self, code, reason=None):
        log.debug("Connection closed with code:\n%s\nAnd reason:\n%s" % (code, reason))

    def received_message(self, m):
        try:
            msgObj = json.loads(m.data.decode('utf-8'))
            if "replay" in msgObj:
                f = self.__returnFunctions.get(msgObj["ID"], None)
                if f and msgObj["success"]:
                    f.onSuccess(msgObj["replay"])
                elif f and f.onError:
                    f.onError(msgObj["replay"])
            else:
                self.api.__getattribute__(msgObj["hub"]).client.__dict__[msgObj["function"]](*msgObj["args"])
        except Exception as e:
            self.onError(e)

    def getReturnFunction(self, ID):
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
            r = Timer(self.serverTimeout, self.onTimeOut, (ID,))
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

class HubsAPI(object):
    def __init__(self, url, serverTimeout=5.0):
        self.wsClient = WSHubsAPIClient(self, url, serverTimeout)
        self.ChatHub = self.__ChatHub(self.wsClient)

    def connect(self):
        self.wsClient.connect()


    class __ChatHub(object):
        def __init__(self, wsClient):
            hubName = self.__class__.__name__[2:]
            self.server = self.__Server(wsClient, hubName)
            self.client = WSSimpleObject()

        class __Server(GenericServer):
            
            def getNumOfClientsConnected(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "getNumOfClientsConnected", "args": args, "ID": id}
                self.wsClient.send(json.dumps(self._serializeObject(body)))
                return self.wsClient.getReturnFunction(id)
        
            def sendToAll(self, name, message):
                """
                :rtype : WSReturnObject
                """
                args = list()
                args.append(name)
                args.append(message)
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "sendToAll", "args": args, "ID": id}
                self.wsClient.send(json.dumps(self._serializeObject(body)))
                return self.wsClient.getReturnFunction(id)
        
