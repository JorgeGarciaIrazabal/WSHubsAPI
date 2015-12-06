__author__ = 'Jorge'


class HubException(Exception):
    pass


class Hub(object):
    HUBs_DICT = {}

    def __init__(self):
        hubName = self.__class__.__dict__.get("__HubName__", self.__class__.__name__)
        if hubName in self.HUBs_DICT:
            raise HubException("Hub's name must be unique")
        if hubName.startswith("__"):
            raise HubException("Hub's name can not start with '__'")
        if hubName == "wsClient":
            raise HubException("Hub's name can not be 'wsClient', it is a  reserved name")
        setattr(self.__class__, "__HubName__", hubName)
        self.HUBs_DICT[hubName] = self

    @classmethod
    def setClientsHolder(cls, clientsHolder):
        """
        :type clientsHolder: WSHubsAPI.ConnectedClientsHolder.ConnectedClientsHolder
        """
        cls._clientsHolder = clientsHolder