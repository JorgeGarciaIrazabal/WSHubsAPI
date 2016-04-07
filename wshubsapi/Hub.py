__author__ = 'Jorge'


class UnsuccessfulReplay:
    def __init__(self, replay):
        self.replay = replay


class HubError(Exception):
    pass


class Hub(object):
    __hubSubscribers = []

    def __init__(self):
        hub_name = self.__class__.__dict__.get("__HubName__", self.__class__.__name__)
        if hub_name in HubsInspector.HUBs_DICT:
            raise HubError("Hub's name must be unique")
        if hub_name.startswith("__"):
            raise HubError("Hub's name can not start with '__'")
        if hub_name == "wsClient":
            raise HubError("Hub's name can not be 'wsClient', it is a  reserved name")
        setattr(self.__class__, "__HubName__", hub_name)
        HubsInspector.HUBs_DICT[hub_name] = self

        self._client_functions = dict()
        self._define_client_functions()
        self.__class__._clients_holder = ConnectedClientsHolder(hub_name)

    def subscribe_to_hub(self, _sender):
        if _sender in self.__hubSubscribers:
            return False
        self.__hubSubscribers.append(_sender)
        return True

    def unsubscribe_from_hub(self, _sender):
        if _sender in self.__hubSubscribers:
            self.__hubSubscribers.remove(_sender)
            return True
        return False

    def get_subscribed_clients_to_hub(self):
        self.__hubSubscribers = list(filter(lambda c: not c.api_isClosed, self.__hubSubscribers))
        return map(lambda x: x.ID, self.__hubSubscribers)

    @classmethod
    def _get_clients_holder(cls):
        """
        :rtype: ConnectedClientsHolder
        """
        # clientsHolder is defined while inspecting hubs
        # can not be initialized in Hub because it is independent in each subHub
        return cls._clients_holder

    @property
    def client_functions(self):
        return self._client_functions

    @client_functions.setter
    def client_functions(self, client_functions):
        assert isinstance(client_functions, dict)
        for functionName, function in client_functions.items():
            assert isinstance(functionName, basestring)
            assert hasattr(function, '__call__')
        self._client_functions = client_functions

    @staticmethod
    def _construct_unsuccessful_replay(replay):
        return UnsuccessfulReplay(replay)

    def _define_client_functions(self):
        pass


from wshubsapi.HubsInspector import HubsInspector
from wshubsapi.ConnectedClientsHolder import ConnectedClientsHolder
