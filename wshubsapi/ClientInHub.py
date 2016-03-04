from wshubsapi import utils

"""
Class that wraps a client but includes de hubName to be able to construct the message to call client function
"""


class ClientInHub(object):
    def __init__(self, client, hubName):
        """
        :type client: wshubsapi.ConnectedClient.ConnectedClient
        :type hubName: str
        """
        self.__hubName = str(hubName)
        self.__client = client
        self.__comEnvironment = client.api_getCommEnvironment()

    def __getattr__(self, item):
        """
        :param item: function name defined in the client side ("item" name keep because it is a magic function)
        """
        if item in self.__client.__dict__:
            return self.__client.__dict__[item]
        else:
            if item.startswith("__") and item.endswith("__"):
                return
            if "_ClientInHub" + item in self.__dict__:
                return self.__dict__["_ClientInHub" + item]
            return self.__constructFunctionToSendMessageToClient(item)

    def __constructFunctionToSendMessageToClient(self, functionName):
        def connectionFunction(*args):
            message = dict(function=functionName, args=list(args), hub=self.__hubName,
                           ID=self.__comEnvironment.getNewMessageID())
            msgStr = utils.serializeMessage(self.__comEnvironment.pickler, message)
            self.api_writeMessage(msgStr)

        return connectionFunction

    def __setattr__(self, key, value):
        if key.startswith("_ClientInHub__") or key.startswith("__"):
            super(ClientInHub, self).__setattr__(key, value)
            return
        self.__client.__dict__[key] = value

    def api_getRealConnectedClient(self):
        return self.__client
