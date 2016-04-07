import json
import logging
import threading
from threading import Timer
import jsonpickle
from jsonpickle.pickler import Pickler
from wshubsapi import utils

utils.set_serializer_date_handler()
_defaultPickler = Pickler(max_depth=4, max_iter=100, make_refs=False)


class WSSimpleObject(object):
    def __setattr__(self, key, value):
        return super(WSSimpleObject, self).__setattr__(key, value)


class WSReturnObject:
    class WSCallbacks:
        def __init__(self, onSuccess=None, onError=None):
            self.onSuccess = onSuccess
            self.onError = onError
            self.onFinally = lambda: None

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


def constructAPIClientClass(clientClass):
    if clientClass is None:
        from ws4py.client.threadedclient import WebSocketClient
        clientClass = WebSocketClient
    class WSHubsAPIClient(clientClass):
        def __init__(self, api, url, serverTimeout):
            """
            :type api: HubsAPI
            """
            clientClass.__init__(self, url)
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
                try:
                    if f and msgObj["success"]:
                        f.onSuccess(msgObj["replay"])
                    elif f and f.onError:
                        f.onError(msgObj["replay"])
                finally:
                    if f:
                        f.onFinally()
            else:
                try:
                    clientFunction = self.api.__getattribute__(msgObj["hub"]).client.__dict__[msgObj["function"]]
                    replayMessage = dict(ID=msgObj["ID"])
                    try:
                        replay = clientFunction(*msgObj["args"])
                        replayMessage["replay"] = replay
                        replayMessage["success"] = True
                    except Exception as e:
                        replayMessage["replay"] = str(e)
                        replayMessage["success"] = False
                    finally:
                        self.api.wsClient.send(self.api.serializeObject(replayMessage))
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
                return callBacks

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

    return WSHubsAPIClient


class HubsAPI(object):
    def __init__(self, url, serverTimeout=5.0, clientClass=None, pickler=_defaultPickler):
        apiClientClass = constructAPIClientClass(clientClass)
        self.wsClient = apiClientClass(self, url, serverTimeout)
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

    def serializeObject(self, obj2ser):
        return jsonpickle.encode(self.pickler.flatten(obj2ser))


    class __ChatHub(object):
        def __init__(self, wsClient, pickler):
            hubName = self.__class__.__name__[2:]
            self.server = self.__Server(wsClient, hubName, pickler)
            self.client = WSSimpleObject()

        class __Server(GenericServer):
            
            def class_method(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "class_method", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def get_subscribed_clients_to_hub(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "get_subscribed_clients_to_hub", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def send_to_all(self, name, message="hello"):
                """
                :rtype : WSReturnObject
                """
                args = list()
                args.append(name)
                args.append(message)
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "send_to_all", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def static_func(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "static_func", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def subscribe_to_hub(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "subscribe_to_hub", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def unsubscribe_from_hub(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "unsubscribe_from_hub", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
    class __UtilsAPIHub(object):
        def __init__(self, wsClient, pickler):
            hubName = self.__class__.__name__[2:]
            self.server = self.__Server(wsClient, hubName, pickler)
            self.client = WSSimpleObject()

        class __Server(GenericServer):
            
            def get_hubs_structure(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "get_hubs_structure", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def get_id(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "get_id", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def get_subscribed_clients_to_hub(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "get_subscribed_clients_to_hub", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def is_client_connected(self, client_id):
                """
                :rtype : WSReturnObject
                """
                args = list()
                args.append(client_id)
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "is_client_connected", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def set_id(self, client_id):
                """
                :rtype : WSReturnObject
                """
                args = list()
                args.append(client_id)
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "set_id", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def subscribe_to_hub(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "subscribe_to_hub", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        
            def unsubscribe_from_hub(self, ):
                """
                :rtype : WSReturnObject
                """
                args = list()
                
                id = self._getNextMessageID()
                body = {"hub": self.hubName, "function": "unsubscribe_from_hub", "args": args, "ID": id}
                retFunction = self.wsClient.getReturnFunction(id)
                self.wsClient.send(self._serializeObject(body))
                return retFunction
        