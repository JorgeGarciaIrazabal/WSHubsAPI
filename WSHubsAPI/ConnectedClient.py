import logging
import jsonpickle
from WSHubsAPI.FunctionMessage import FunctionMessage

log = logging.getLogger(__name__)


class ConnectedClient(object):
	def __init__(self, client, serializationPickler, commProtocol):
		"""
		:type commProtocol: WSHubsAPI.CommProtocol.CommProtocol
		"""
		self.ID = None
		""":type : int|None|str"""
		self.client = client
		self.pickler = serializationPickler
		self.__commProtocol = commProtocol

	def onOpen(self, ID=None):
		with self.__commProtocol.lock:
			if ID is None or ID in self.__commProtocol.allConnectedClients:
				self.ID = self.__commProtocol.getUnprovidedID()
			else:
				self.ID = ID
			self.__commProtocol.allConnectedClients[self.ID] = self
			return self.ID

	def onMessage(self, message):
		try:
			msg = FunctionMessage(message, self)
			replay = msg.callFunction()
			if replay is not None:
				self.onReplay(replay, msg)
		except Exception as e:
			self.onError(e)

	def onAsyncMessage(self, message):
		self.__commProtocol.wsMessageReceivedQueue.put((message, self))

	def onClose(self):
		if self.ID in self.__commProtocol.allConnectedClients.keys():
			self.__commProtocol.allConnectedClients.pop(self.ID)
			if isinstance(self.ID, str) and self.ID.startswith(
					"UNPROVIDED__"):  # todo, need a regex to check if is unprovided
				self.__commProtocol.availableUnprovidedIds.append(self.ID)

	def onError(self, exception):
		log.exception("Error parsing message")

	def onReplay(self, replay, message):
		"""
		:param replay: serialized object to be sent as a replay of a message received
		:param message: Message received (provided for overridden functions)
		"""
		self.writeMessage(self.serializeMessage(replay))

	def __getattr__(self, item):
		if item.startswith("__") and item.endswith("__"):
			return

		def connectionFunction(*args, **kwargs):
			message = {"function": item, "args": list(args), "hub": kwargs["hubName"]}
			msgStr = self.serializeMessage(message)
			self.writeMessage(msgStr)

		return connectionFunction

	def writeMessage(self, *args, **kwargs):
		raise NotImplementedError

	def serializeMessage(self, message):
		return jsonpickle.encode(self.pickler.flatten(message))


class ConnectedClientsGroup:
	def __init__(self, connectedClientsInGroup, hubName):
		"""
		:type connectedClientsInGroup: list of ConnectedClient
		"""
		self.hubName = hubName
		self.connectedClients = connectedClientsInGroup

	def append(self, p_object):
		if isinstance(p_object, ConnectedClient):
			self.connectedClients.append(p_object)
		else:
			raise TypeError()

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
