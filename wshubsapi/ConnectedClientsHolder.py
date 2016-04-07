
class ConnectedClientsHolder:
    allConnectedClientsDict = dict()

    def __init__(self, hubName):
        self.hubName = hubName

    def getAllClients(self):
        return ConnectedClientsGroup(list(self.allConnectedClientsDict.values()), self.hubName)

    def getOtherClients(self, sender):
        """
        :type sender: ConnectedClientsGroup
        """
        connectedClients = [c for c in self.allConnectedClientsDict.values() if c.ID != sender.ID]
        return ConnectedClientsGroup(connectedClients, self.hubName)

    def getClients(self, filterFunction):
        return ConnectedClientsGroup([c for c in self.allConnectedClientsDict.values() if filterFunction(c)], self.hubName)

    def getClient(self, clientId):
        return ConnectedClientsGroup([self.allConnectedClientsDict[clientId]], self.hubName)[0]

    def getSubscribedClients(self):
        subscribedClients = HubsInspector.get_hub_instance(self.hubName).get_subscribed_clients_to_hub()
        return ConnectedClientsGroup([self.allConnectedClientsDict[ID] for ID in subscribedClients], self.hubName)

    @classmethod
    def appendClient(cls, client):
        cls.allConnectedClientsDict[client.ID] = client

    @classmethod
    def popClient(cls, clientId):
        """
        :type clientId: str|int
        """
        return cls.allConnectedClientsDict.pop(clientId, None)


from wshubsapi.ConnectedClientsGroup import ConnectedClientsGroup
from wshubsapi.HubsInspector import HubsInspector
