import json
import logging
from WSHubsAPI.Hub import Hub

log = logging.getLogger(__name__)


class FunctionMessage:
	def __init__(self, messageStr, connectedClient):
		"""
		:type messageStr: bytes|str
		"""
		messageStr = messageStr if isinstance(messageStr, str) else messageStr.decode("utf-8")
		msgObj = json.loads(messageStr)
		self.cls = Hub.HUBs_DICT[msgObj["hub"]]
		self.HubName = msgObj["hub"]
		self.args = msgObj["args"]
		self.connectedClient = connectedClient

		self.functionName = msgObj["function"]
		self.method = getattr(self.cls, self.functionName)
		self.messageID = msgObj.get("ID", -1)

	def __executeFunction(self):
		try:
			return True, self.method(*self.args, _sender=self.connectedClient)
		except Exception as e:
			log.exception("Error calling hub function")
			return False, str(e)

	def callFunction(self):
		success, replay = self.__executeFunction()
		if replay is not None:
			return self.getReplayDict(success, replay)

	def getReplayDict(self, success=None, replay=None):
		return {
			"success": success,
			"replay": replay,
			"hub": self.HubName,
			"function": self.functionName,
			"ID": self.messageID
		}
