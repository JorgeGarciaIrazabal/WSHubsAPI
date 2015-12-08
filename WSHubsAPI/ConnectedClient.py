import logging

import utils
from WSHubsAPI.FunctionMessage import FunctionMessage

log = logging.getLogger(__name__)


class ConnectedClient(object):
    def __init__(self, client, serializationPickler, commProtocol):
        """
        :type commProtocol: WSHubsAPI.CommProtocol.CommProtocol | None
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
        self.writeMessage(utils.serializeMessage(self.pickler, replay))

    def writeMessage(self, *args, **kwargs):
        raise NotImplementedError
