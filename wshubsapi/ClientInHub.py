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
        self.__hubName = hubName
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
            return self.__constructFunctionToSendMessageToClient(item)

    def __constructFunctionToSendMessageToClient(self, functionName):
        def connectionFunction(*args):
            message = {"function": functionName, "args": list(args), "hub": self.hubName}
            msgStr = utils.serializeMessage(self.__comEnvironment.pickler, message)
            self.api_writeMessage(msgStr)

        return connectionFunction

    def __setattr__(self, key, value):
        if key.startswith("_ClientInHub__"):
            super(ClientInHub, self).__setattr__(key, value)
            return
        self.__client.__dict__[key] = value

    def api_getRealConnectedClient(self):
        return self.__client
