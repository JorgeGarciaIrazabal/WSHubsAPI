import logging

from wshubsapi import utils
from wshubsapi.ConnectedClientsHolder import ConnectedClientsHolder
from wshubsapi.FunctionMessage import FunctionMessage

log = logging.getLogger(__name__)


# Change class name //WSAPIClient? WSHUBsClient? ConnHandler?
class ConnectedClient(object):
    def __init__(self, communication_environment, write_message_function):
        """
        :type communication_environment: WSHubsAPI.CommEnvironment.CommEnvironment | None
        """
        self.ID = None
        """:type : int|None|str"""
        self.api_write_message = write_message_function
        self.api_is_closed = False
        self.__communication_environment = communication_environment

    def api_get_comm_environment(self):
        return self.__communication_environment
