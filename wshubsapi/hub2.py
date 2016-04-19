from wshubsapi.connected_clients_group import ConnectedClientsGroup
from wshubsapi.connected_clients_holder import ConnectedClientsHolder

__author__ = 'Jorge'


class UnsuccessfulReplay:
    def __init__(self, replay):
        self.replay = replay


class Hub(object):
    def __init__(self):
        hub_name = self.__class__.__dict__.get("__HubName__", self.__class__.__name__)
        setattr(self.__class__, "__HubName__", hub_name)

        self._client_functions = dict()
        self._define_client_functions()
        self._clients_holder = ConnectedClientsHolder(self)
        self.__hub_subscribers = []

    def subscribe_to_hub(self, _sender):
        if _sender.api_get_real_connected_client() in self.__hub_subscribers:
            return False
        self.__hub_subscribers.append(_sender.api_get_real_connected_client())
        return True

    def unsubscribe_from_hub(self, _sender):
        """
        :type _sender: ClientInHub
        """
        real_connected_client = _sender.api_get_real_connected_client()
        if real_connected_client in self.__hub_subscribers:
            self.__hub_subscribers.remove(real_connected_client)
            return True
        return False

    def get_subscribed_clients_to_hub(self):
        self.__hub_subscribers = list(filter(lambda c: not c.api_is_closed, self.__hub_subscribers))
        return ConnectedClientsGroup(self.__hub_subscribers, self.__HubName__)

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
            assert isinstance(function_name, basestring)
            assert hasattr(function, '__call__')
        self._client_functions = client_functions

    @staticmethod
    def _construct_unsuccessful_replay(replay):
        return UnsuccessfulReplay(replay)

    def _define_client_functions(self):
        pass
