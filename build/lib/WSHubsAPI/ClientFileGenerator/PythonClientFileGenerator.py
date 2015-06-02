import inspect
import os
from WSHubsAPI.utils import isNewFunction, getDefaults, getArgs

__author__ = 'jgarc'

class PythonClientFileGenerator():
    FILE_NAME = "WSProtocol.py"
    TAB = "    "

    @classmethod
    def __getHubClassStr(cls, class_):
        funcStrings = ("\n" + cls.TAB * 2).join(cls.__getFunctionStr(class_))
        return cls.CLASS_TEMPLATE.format(name=class_.__HubName__, functions=funcStrings)

    @classmethod
    def __getFunctionStr(cls, class_):
        funcStrings = []
        functions = inspect.getmembers(class_, predicate=isNewFunction)
        for name, method in functions:
            args = getArgs(method)
            defaults = getDefaults(method)
            formattedArgs = []
            for i, arg in enumerate(reversed(args)):
                if i >= len(defaults):
                    formattedArgs.insert(0, arg)
                else:
                    formattedArgs.insert(0, arg + "=" + str(defaults[-i - 1]))
            appendInArgs = ("\n" + cls.TAB * 3).join([cls.ARGS_COOK_TEMPLATE.format(name=arg) for arg in args])
            funcStrings.append(
                cls.FUNCTION_TEMPLATE.format(name=name, args=", ".join(formattedArgs), cook=appendInArgs))
        return funcStrings

    @classmethod
    def __getClientHubsStrings(cls, hubs):
        return [cls.CLIENT_HUB_TEMPLATE.format(name=h.__HubName__) for h in hubs]

    @classmethod
    def createFile(cls, path, hubs):
        with open(os.path.join(path, cls.FILE_NAME), "w") as f:
            classStrings = "".join(cls.__getClassStrings(hubs))
            clientHubs = "\n".join(cls.__getClientHubsStrings(hubs))
            f.write(cls.WRAPPER.format(main=classStrings, clientHubs=clientHubs))

    @classmethod
    def __getClassStrings(cls, hubs):
        classStrings = []
        for h in hubs:
            classStrings.append(cls.__getHubClassStr(h))
        return classStrings

    WRAPPER = '''from __future__ import print_function
import json
import logging
import threading
from ws4py.client.threadedclient import WebSocketClient
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
{clientHubs}

class WSServer(object):
    _messageID = 0
    _messageLock = threading.RLock()

    @classmethod
    def getNextMessageID(cls):
        with cls._messageLock:
            cls._messageID += 1
            return cls._messageID
    {main}

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
        log.debug("Connection closed with code:\\n%s\\nAnd reason:\\n%s"%(code,reason))

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
'''

    CLASS_TEMPLATE = '''
    class {name}(object):
        {functions}
        '''
    FUNCTION_TEMPLATE = '''
        @classmethod
        def {name}(cls, {args}):
            """
            :rtype : WSReturnObject
            """
            args = list()
            {cook}
            id = WSServer.getNextMessageID()
            body = {{"hub": cls.__name__, "function": "{name}", "args": args, "ID": id}}
            WSConnection._instance.send(json.dumps(body))
            return WSConnection._instance._getReturnFunction(id)'''
    ARGS_COOK_TEMPLATE = "args.append({name})"
    CLIENT_HUB_TEMPLATE = "    {name} = WSSimpleObject()"
