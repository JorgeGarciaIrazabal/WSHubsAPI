import json
import logging
import threading
from threading import Timer
import jsonpickle
from jsonpickle.pickler import Pickler
from ws4py.client.threadedclient import WebSocketClient
from wshubsapi import utils

utils.setSerializerDateTimeHandler()

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

    def __init__(self, wsClient, hubName, pickler):
        """
        :type wsClient: WSHubsAPIClient
        """
        self.wsClient = wsClient
        self.hubName = hubName
        self.pickler = pickler

    @classmethod
    def _getNextMessageID(cls):
        with cls.__messageLock:
            cls.__messageID += 1
            return cls.__messageID

    def _serializeObject(self, obj2ser):
        return jsonpickle.encode(self.pickler.flatten(obj2ser))


class WSHubsAPIClient(WebSocketClient):
    def __init__(self, api, url, serverTimeout):
        super(WSHubsAPIClient, self).__init__(url)
        self.__returnFunctions = dict()
        self.isOpened = False
        self.serverTimeout = serverTimeout
        self.api = api
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())

    def opened(self):
        self.isOpened = True
        self.log.debug("Connection opened")

    def closed(self, code, reason=None):
        self.log.debug("Connection closed with code:\n%s\nAnd reason:\n%s" % (code, reason))

    def received_message(self, m):
        try:
            msgObj = json.loads(m.data.decode('utf-8'))
        except Exception as e:
            self.onError(e)
            return
        if "replay" in msgObj:
            f = self.__returnFunctions.get(msgObj["ID"], None)
            if f and msgObj["success"]:
                f.onSuccess(msgObj["replay"])
            elif f and f.onError:
                f.onError(msgObj["replay"])
        else:
            try:
                clientFunction = self.api.__getattribute__(msgObj["hub"]).client.__dict__[msgObj["function"]]
                clientFunction(*msgObj["args"])
            except:
                pass


        self.log.debug("Received message: %s" % m.data.decode('utf-8'))

    def getReturnFunction(self, ID):
        """
        :rtype : WSReturnObject
        """

        def returnFunction(onSuccess, onError=None, timeOut=None):
            callBacks = self.__returnFunctions.get(ID, WSReturnObject.WSCallbacks())
            onError = onError if onError is not None else self.defaultOnError

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

            timeOut = timeOut if timeOut is not None else self.serverTimeout
            r = Timer(timeOut, self.onTimeOut, (ID,))
            r.start()

        retObject = WSReturnObject()
        retObject.done = returnFunction

        # todo create timeout
        return retObject

    def onError(self, exception):
        self.log.exception("Error in protocol")

    def onTimeOut(self, messageId):
        f = self.__returnFunctions.pop(messageId, None)
        if f and f.onError:
            f.onError("timeOut Error")

    def defaultOnError(self, error):
        pass

class HubsAPI(object):
    def __init__(self, url, serverTimeout=5.0, pickler=Pickler(max_depth=4, max_iter=100, make_refs=False)):
        self.wsClient = WSHubsAPIClient(self, url, serverTimeout)
        self.wsClient.defaultOnError = lambda error: None
        self.pickler = pickler
        self.ChatHub = self.__ChatHub(self.wsClient, self.pickler)
        self.UtilsAPIHub = self.__UtilsAPIHub(self.wsClient, self.pickler)

    @property
    def defaultOnError(self):
        return None

    @defaultOnError.setter
    def defaultOnError(self, func):
        self.wsClient.defaultOnError = func

    def connect(self):
        self.wsClient.connect()


    class __ChatHub(object):
        def __init__(self, wsClient, pickler):
            hubName = self.__class__.__name__[2:]
            self.server = self.__Server(wsClient, hubName, pickler)
            self.client = WSSimpleObject()

        class __Server(GenericServer):
            
            def classMethod(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "classMethod", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def getSubscribedClientsToHub(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "getSubscribedClientsToHub", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def sendToAll(self, name, message="hello"):
                """
                :rtype : WSReturnObject
                """
                args = list()
                args.append(name)
                args.append(message)
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "sendToAll", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def staticFunc(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "staticFunc", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def subscribeToHub(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "subscribeToHub", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def unsubscribeFromHub(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "unsubscribeFromHub", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
    class __UtilsAPIHub(object):
        def __init__(self, wsClient, pickler):
            hubName = self.__class__.__name__[2:]
            self.server = self.__Server(wsClient, hubName, pickler)
            self.client = WSSimpleObject()

        class __Server(GenericServer):
            
            def getHubsStructure(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "getHubsStructure", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def getId(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "getId", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def getSubscribedClientsToHub(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "getSubscribedClientsToHub", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def isClientConnected(self, clientId):
                """
                :rtype : WSReturnObject
                """
                args = list()
                args.append(clientId)
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "isClientConnected", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def setId(self, clientId):
                """
                :rtype : WSReturnObject
                """
                args = list()
                args.append(clientId)
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "setId", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def subscribeToHub(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "subscribeToHub", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def unsubscribeFromHub(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "unsubscribeFromHub", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
