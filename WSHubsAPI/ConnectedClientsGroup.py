class ConnectedClientsGroup:
	def __init__(self, connectedClientsInGroup, hubName):
		"""
		:type connectedClientsInGroup: list of ConnectedClient
		"""
		self.hubName = hubName
		self.connectedClients = connectedClientsInGroup

	def append(self, p_object):
		"""
		:type p_object: ConnectedClient.ConnectedClient
		"""
		self.connectedClients.append(p_object)

	def __getattr__(self, item):
		functions = []
		for c in self.connectedClients:
			functions.append(c.__getattr__(item))

		def connectionFunctions(*args):
			for f in functions:
				f(*args, hubName=self.hubName)

		return connectionFunctions

	def __getitem__(self, item):
		"""
		:rtype : ConnectedClient
		"""
		return self.connectedClients.__getitem__(item)

	def __len__(self):
		return self.connectedClients.__len__()
