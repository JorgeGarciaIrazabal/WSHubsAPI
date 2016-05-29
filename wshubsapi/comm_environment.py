import json
import logging
import threading

try:
    from Queue import Queue
except:
    from queue import Queue
from jsonpickle.pickler import Pickler
from concurrent.futures import Future

from wshubsapi.connected_clients_holder import ConnectedClientsHolder
from wshubsapi.function_message import FunctionMessage
from wshubsapi.utils import set_serializer_date_handler, serialize_message
from wshubsapi.messages_received_queue import MessagesReceivedQueue
# do not remove this line (hubs inspector needs to find it)
from wshubsapi import utils_api_hub, asynchronous

log = logging.getLogger(__name__)
__author__ = 'Jorge Garcia Irazabal'

_DEFAULT_PICKER = Pickler(max_depth=5, max_iter=80, make_refs=False)

set_serializer_date_handler()  # todo move this


class HubsApiException(Exception):
    pass


class CommEnvironment(object):
    _comm_environments = dict()
    get_instance_lock = threading.Lock()

    def __init__(self, message_received_queue_class=None,
                 unprovided_id_template="UNPROVIDED__{}",
                 serialization_max_depth=5,
                 serialization_max_iter=80,
                 debug_mode=True):
        """
        :type message_received_queue_class: MessagesReceivedQueue
        """
        self.lock = threading.Lock()
        self.available_unprovided_ids = list()
        self.unprovided_id_template = unprovided_id_template
        self.last_provided_id = 0
        self.debug_mode = debug_mode

        if message_received_queue_class is None:
            self.message_received_queue = MessagesReceivedQueue()
        else:
            self.message_received_queue = message_received_queue_class
        self.message_received_queue.on_message = self.on_message
        self.message_received_queue.on_error = self.on_error

        self.message_received_queue.start_threads()
        self.all_connected_clients = ConnectedClientsHolder.all_connected_clients
        self.serialization_args = dict(max_depth=serialization_max_depth, max_iter=serialization_max_iter)
        self.__last_client_message_id = 0
        self.__new_client_message_id_lock = threading.Lock()
        self.__futures_buffer = {}
        """:type : dict[int, Future, datetime]"""

    def get_unprovided_id(self):
        if len(self.available_unprovided_ids) > 0:
            return self.available_unprovided_ids.pop(0)
        while self.unprovided_id_template.format(self.last_provided_id) in self.all_connected_clients:
            self.last_provided_id += 1
        return self.unprovided_id_template.format(self.last_provided_id)

    def on_opened(self, client, id_=None):
        with self.lock:
            if id_ is None or id_ in self.all_connected_clients:
                client.ID = self.get_unprovided_id()
            else:
                client.ID = id_
            ConnectedClientsHolder.append_client(client)
            return client.ID

    def on_message(self, client, msg_str):
        try:
            msg_str = msg_str if isinstance(msg_str, str) else msg_str.encode("utf-8")
            msg_obj = json.loads(msg_str)
            if "reply" not in msg_obj:
                self.__on_replay(client, msg_str, msg_obj)
            else:
                self.__on_replayed(msg_obj)

        except Exception as e:
            self.on_error(client, e)

    def on_async_message(self, client, message):
        self.message_received_queue.put((message, client))

    def on_closed(self, client):
        """:type client: wshubsapi.connected_client.ConnectedClient"""
        ConnectedClientsHolder.pop_client(client.ID)
        client.api_is_closed = True

    def on_error(self, client, exception):
        log.exception("Error parsing message")

    def reply(self, client, reply, origin_message):
        """
        :type client: wshubsapi.connected_client.ConnectedClient
        :param reply: serialized object to be sent as a reply of a message received
        :param origin_message: Message received (provided for overridden functions)
        """
        client.api_write_message(serialize_message(self.serialization_args, reply))

    def get_new_clients_future(self):
        with self.__new_client_message_id_lock:
            self.__last_client_message_id += 1
            id_ = self.__last_client_message_id
            self.__futures_buffer[id_] = Future()
        return self.__futures_buffer[id_], id_

    def close(self, **kwargs):
        self.message_received_queue.executor.shutdown(**kwargs)

    @classmethod
    def get_instance(cls, key="generic", **kwargs):
        """
        :key: include a key to use multiple communication environments
        :rtype: CommEnvironment
        """
        with cls.get_instance_lock:
            cls._comm_environments[key] = cls._comm_environments.get(key, None)
            if cls._comm_environments[key] is None:
                cls._comm_environments[key] = CommEnvironment(**kwargs)
            return cls._comm_environments[key]

    def __on_time_out(self, id_):
        with self.__new_client_message_id_lock:
            if id_ in self.__futures_buffer:
                future = self.__futures_buffer.pop(id_)
                future.set_exception(HubsApiException("Timeout exception"))

    def __on_replay(self, client, msg_str, msg_obj):
        hub_function = FunctionMessage(msg_obj, client, self)
        reply = hub_function.call_function()
        if reply is not None:
            self.reply(client, reply, msg_str)

    def __on_replayed(self, msg_obj):
        future = self.__futures_buffer.pop(msg_obj["ID"], None)
        if future is not None:
            if msg_obj["success"]:
                future.set_result(msg_obj["reply"])
            else:
                future.set_exception(Exception(msg_obj["reply"]))
