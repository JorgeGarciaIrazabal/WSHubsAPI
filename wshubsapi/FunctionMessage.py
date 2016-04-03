import logging
import traceback

from wshubsapi.ClientInHub import ClientInHub
from wshubsapi.Hub import UnsuccessfulReplay
from wshubsapi.HubsInspector import HubsInspector
from wshubsapi.utils import getArgs, SENDER_KEY_PARAMETER

log = logging.getLogger(__name__)


class FunctionMessage:
    def __init__(self, msgObj, connectedClient):
        """
        :type messageStr: bytes|str
        """
        self.hubInstance = HubsInspector.HUBs_DICT[msgObj["hub"]]
        self.hubName = msgObj["hub"]
        self.args = msgObj["args"]
        self.connectedClient = connectedClient

        self.functionName = msgObj["function"]
        self.method = getattr(self.hubInstance, self.functionName)
        self.messageID = msgObj.get("ID", -1)

    def __executeFunction(self):
        try:
            self.__includeSenderInArgs(self.method, self.args)
            return True, self.method(*self.args)
        except Exception as e:
            log.exception("Error calling hub function with: {}".format(str(self)))
            return False, dict(error=str(e), type=str(type(e)), trace=traceback.format_exc())

    def callFunction(self):
        success, replay = self.__executeFunction()
        if isinstance(replay, UnsuccessfulReplay):
            return self.constructReplayDict(False, replay.replay)
        return self.constructReplayDict(success, replay)

    def constructReplayDict(self, success=None, replay=None):
        return {
            "success": success,
            "replay": replay,
            "hub": self.hubName,
            "function": self.functionName,
            "ID": self.messageID
        }

    def __includeSenderInArgs(self, method, args):
        """
        :type args: list
        """
        methodArgs = getArgs(method, includeSender=True)
        try:
            senderIndex = methodArgs.index(SENDER_KEY_PARAMETER)
            args.insert(senderIndex, ClientInHub(self.connectedClient, self.hubName))
        except ValueError:
            pass

    def __str__(self):
        return """
HubName = {0}
FunctionName = {1}
args = {2}
messageID = {3}""".format(self.hubName, self.functionName, str(self.args), self.messageID)
