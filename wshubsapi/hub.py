from concurrent.futures import Future

from wshubsapi import utils
from wshubsapi.connected_clients_holder import ConnectedClientsHolder

__author__ = 'Jorge'


class UnsuccessfulReplay:
    def __init__(self, reply):
        self.reply = reply


class Hub(object):
    __HubName__ = None

    def __init__(self):
        hub_name = self.__class__.__dict__.get("__HubName__", self.__class__.__name__)
        setattr(self.__class__, "__HubName__", hub_name)

        self._client_functions = self._define_client_functions()
        self._clients_holder = ConnectedClientsHolder(self)
        setattr(self.__class__, "__instance__", self)

    def subscribe_to_hub(self, _sender):
        if _sender.api_get_real_connected_client() in self._clients_holder.hub_subscribers:
            return False
        self._clients_holder.hub_subscribers.append(_sender.api_get_real_connected_client())
        return True

    def unsubscribe_from_hub(self, _sender):
        """
        :type _sender: ClientInHub
        """
        real_connected_client = _sender.api_get_real_connected_client()
        if real_connected_client in self._clients_holder.hub_subscribers:
            self._clients_holder.hub_subscribers.remove(real_connected_client)
            return True
        return False

    def get_subscribed_clients_ids(self):
        return [c.ID for c in self._clients_holder.get_subscribed_clients()]

    @property
    def clients(self):
        return self._clients_holder

    @property
    def client_functions(self):
        return self._client_functions

    @client_functions.setter
    def client_functions(self, client_functions):
        assert isinstance(client_functions, dict)
        for function_name, function in client_functions.items():
            assert isinstance(function_name, utils.string_class)
            assert hasattr(function, '__call__')
        self._client_functions = client_functions

    @staticmethod
    def _construct_unsuccessful_replay(reply):
        return UnsuccessfulReplay(reply)

    def _define_client_functions(self):
        """
        This function will tell the client possible client functions to be called from sever
        It is just to inform, it is not mandatory but recommended

        :return: It has to return a dict with:
            key: function name,
            value: lambda with the function structure (args and default values)
            example:
            return dict(post_message=lambda message, thread="MAIN": None,
                        change_picture=lambda picture_url: None)
        """
        return dict()

    @classmethod
    def get_instance(cls):
        """
        HUBS_API_IGNORE
        """
        return cls.__instance__

    def _client_to_clients_bridge(self, clients_ids, function, args):
        clients = self.clients.get(clients_ids)
        futures = getattr(clients, function)(*args)
        if isinstance(futures, Future):
            # only one future (ex: if only one client id is provided)
            return futures.result()

        results = dict()
        for future, client in zip(futures, clients.connected_clients):
            try:
                results[client.ID] = future.result(timeout=3)
            except Exception as e:
                results[client.ID] = dict(error_type=e.__class__.__name__, error=str(e))
        return results
