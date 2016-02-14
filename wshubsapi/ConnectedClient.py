import logging

from wshubsapi import utils
from wshubsapi.ConnectedClientsHolder import ConnectedClientsHolder
from wshubsapi.FunctionMessage import FunctionMessage

log = logging.getLogger(__name__)


# Change class name //WSAPIClient? WSHUBsClient? ConnHandler?
class ConnectedClient(object):
    def __init__(self, commEnvironment, writeMessageFunction):
        """
        :type commEnvironment: WSHubsAPI.CommEnvironment.CommEnvironment | None
        """
        self.ID = None
        """:type : int|None|str"""
        self.api_writeMessage = writeMessageFunction
        self.api_isClosed = False
        self.__comEnvironment = commEnvironment

    def api_writeMessage(self, message):
        raise NotImplementedError

    def api_getCommEnvironment(self):
        return self.__comEnvironment
