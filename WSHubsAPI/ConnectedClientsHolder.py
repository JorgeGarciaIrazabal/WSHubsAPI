from WSHubsAPI.ConnectedClientsGroup import ConnectedClientsGroup


class ConnectedClientsHolder:
	allConnectedClients = dict()

	def __init__(self, hubName):
		self.hubName = hubName

	def getAllClients(self):
		return ConnectedClientsGroup(list(self.allConnectedClients.values()), self.hubName)

	def getOtherClients(self, sender):
		return ConnectedClientsGroup([c for c in self.allConnectedClients.values() if c.ID != sender.ID], self.hubName)

	def getClients(self, filterFunction):
		return ConnectedClientsGroup([c for c in self.allConnectedClients.values() if filterFunction(c)], self.hubName)

	def getClient(self, clientId):
		return ConnectedClientsGroup([self.allConnectedClients[clientId]], self.hubName)

	def appendClient(self, client):
		self.allConnectedClients[client.ID] = client

	def popClient(self, clientId):
		"""
		:type clientId: str|int
		"""
		return self.allConnectedClients.pop(clientId, None)
