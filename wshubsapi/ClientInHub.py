from wshubsapi import utils

"""
Class that wraps a client but includes de hubName to be able to construct the message to call client function
"""


class ClientInHub(object):
    def __init__(self, client, hub_name):
        """
        :type client: wshubsapi.ConnectedClient.ConnectedClient
        :type hub_name: str
        """
        self.__hubName = str(hub_name)
        self.__client = client
        self.__comEnvironment = client.api_get_comm_environment()

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
            return self.__construct_function_for_client(item)

    def __construct_function_for_client(self, function_name):
        def connection_function(*args):
            future, id_ = self.__comEnvironment.get_new_clients_future()
            message = dict(function=function_name, args=list(args), hub=self.__hubName,
                           ID=id_)
            msg_str = utils.serialize_message(self.__comEnvironment.pickler, message)
            self.api_writeMessage(msg_str)
            return future

        return connection_function

    def __setattr__(self, key, value):
        if key.startswith("_ClientInHub__") or key.startswith("__"):
            super(ClientInHub, self).__setattr__(key, value)
            return
        self.__client.__dict__[key] = value

    def api_get_real_connected_client(self):
        return self.__client
