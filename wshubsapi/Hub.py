__author__ = 'Jorge'


class UnsuccessfulReplay:
    def __init__(self, replay):
        self.replay = replay


class HubException(Exception):
    pass


class Hub(object):
    __hubSubscribers = []

    def __init__(self):
        hubName = self.__class__.__dict__.get("__HubName__", self.__class__.__name__)
        if hubName in HubsInspector.HUBs_DICT:
            raise HubException("Hub's name must be unique")
        if hubName.startswith("__"):
            raise HubException("Hub's name can not start with '__'")
        if hubName == "wsClient":
            raise HubException("Hub's name can not be 'wsClient', it is a  reserved name")
        setattr(self.__class__, "__HubName__", hubName)
        HubsInspector.HUBs_DICT[hubName] = self

        self._clientFunctions = dict()
        self._defineClientFunctions()
        self.__class__._clientsHolder = ConnectedClientsHolder(hubName)

    def subscribeToHub(self, _sender):
        if _sender in self.__hubSubscribers:
            return False
        self.__hubSubscribers.append(_sender)
        return True

    def unsubscribeFromHub(self, _sender):
        if _sender in self.__hubSubscribers:
            self.__hubSubscribers.remove(_sender)
            return True
        return False

    def getSubscribedClientsToHub(self):
        self.__hubSubscribers = list(filter(lambda c: not c.api_isClosed, self.__hubSubscribers))
        return map(lambda x: x.ID, self.__hubSubscribers)

    @classmethod
    def _getClientsHolder(cls):
        """
        :rtype: ConnectedClientsHolder
        """
        # clientsHolder is defined while inspecting hubs
        # can not be initialized in Hub because it is independent in each subHub
        return cls._clientsHolder

    @property
    def clientFunctions(self):
        return self._clientFunctions

    @clientFunctions.setter
    def clientFunctions(self, clientFunctions):
        assert (isinstance(clientFunctions, dict))
        for functionName, function in clientFunctions.items():
            assert (isinstance(functionName, basestring))
            assert (hasattr(function, '__call__'))
        self._clientFunctions = clientFunctions

    def _constructUnsuccessfulReplay(self, replay):
        return UnsuccessfulReplay(replay)

    def _defineClientFunctions(self):
        pass


from wshubsapi.HubsInspector import HubsInspector
from wshubsapi.ConnectedClientsHolder import ConnectedClientsHolder
