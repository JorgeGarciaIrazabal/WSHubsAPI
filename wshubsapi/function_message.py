import logging
import traceback

from wshubsapi.client_in_hub import ClientInHub
from wshubsapi.hub import UnsuccessfulReplay
from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.utils import get_args, SENDER_KEY_PARAMETER

log = logging.getLogger(__name__)


class FunctionMessage:
    def __init__(self, msg_obj, connected_client, comm_environment):
        """
        :type msg_obj: dict
        :type comm_environment: wshubsapi.comm_environment.CommEnvironment
        """
        self.comm_environment = comm_environment
        self.hub_instance = HubsInspector.HUBS_DICT[msg_obj["hub"]]
        self.hub_name = msg_obj["hub"]
        self.args = msg_obj["args"]
        self.connected_client = connected_client

        self.function_name = msg_obj["function"]
        self.method = getattr(self.hub_instance, self.function_name)
        self.message_id = msg_obj.get("ID", -1)

    def __execute_function(self):
        try:
            self.__include_sender_in_args(self.method, self.args)
            return True, self.method(*self.args)
        except Exception as e:
            log.exception("Error calling hub function with: {}".format(str(self)))
            error_info = dict(error=str(e), type=e.__class__.__name__, trace=traceback.format_exc())
            if not self.comm_environment.debug_mode:
                error_info.pop("trace")
            return False, error_info

    def call_function(self):
        success, reply = self.__execute_function()
        if isinstance(reply, UnsuccessfulReplay):
            return self.construct_replay_dict(False, reply.reply)
        return self.construct_replay_dict(success, reply)

    def construct_replay_dict(self, success=None, reply=None):
        return {
            "success": success,
            "reply": reply,
            "hub": self.hub_name,
            "function": self.function_name,
            "ID": self.message_id
        }

    def __include_sender_in_args(self, method, args):
        """
        :type args: list
        """
        method_args = get_args(method, include_sender=True)
        try:
            sender_index = method_args.index(SENDER_KEY_PARAMETER)
            args.insert(sender_index, ClientInHub(self.connected_client, self.hub_name))
        except ValueError:
            pass

    def __str__(self):
        return """
HubName = {0}
FunctionName = {1}
args = {2}
messageID = {3}""".format(self.hub_name, self.function_name, str(self.args), self.message_id)
