import logging

from wshubsapi import utils
from wshubsapi.connected_clients_holder import ConnectedClientsHolder
from wshubsapi.function_message import FunctionMessage

log = logging.getLogger(__name__)


# Change class name //WSAPIClient? WSHUBsClient? ConnHandler?
class ConnectedClient(object):
    def __init__(self, communication_environment, write_message_function):
        """
        :type communication_environment: WSHubsAPI.comm_environment.CommEnvironment | None
        """
        self.ID = None
        """:type : int|None|str"""
        self.api_write_message = write_message_function
        self.api_is_closed = False
        self.__communication_environment = communication_environment

    def api_get_comm_environment(self):
        return self.__communication_environment
