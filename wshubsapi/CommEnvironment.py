import json
import logging
import threading
from datetime import datetime, timedelta
import time

try:
    from Queue import Queue
except:
    from queue import Queue
from jsonpickle.pickler import Pickler
from concurrent.futures import Future

from wshubsapi.ConnectedClientsHolder import ConnectedClientsHolder
from wshubsapi.FunctionMessage import FunctionMessage
from wshubsapi.utils import set_serializer_date_time_handler, serialize_message
from wshubsapi.MessagesReceivedQueue import MessagesReceivedQueue
# do not remove this line (hubs inspector needs to find it)
from wshubsapi import UtilsAPIHub, Asynchronous

log = logging.getLogger(__name__)
__author__ = 'Jorge Garcia Irazabal'

_DEFAULT_PICKER = Pickler(max_depth=5, max_iter=80, make_refs=False)

set_serializer_date_time_handler()  # todo move this


class HubsApiException(Exception):
    pass


class CommEnvironment(object):
    def __init__(self, max_workers=MessagesReceivedQueue.DEFAULT_MAX_WORKERS,
                 unprovided_id_template="UNPROVIDED__{}", pickler=_DEFAULT_PICKER,
                 client_function_timeout=5):
        self.lock = threading.Lock()
        self.available_unprovided_ids = list()
        self.unprovided_id_template = unprovided_id_template
        self.last_provided_id = 0
        self.message_received_queue = MessagesReceivedQueue(self, max_workers)
        self.message_received_queue.start_threads()
        self.all_connected_clients = ConnectedClientsHolder.all_connected_clients
        self.pickler = pickler
        self.client_function_timeout = client_function_timeout
        self.__last_client_message_id = 0
        self.__new_client_message_id_lock = threading.Lock()
        self.__futures_buffer = {}
        self.__check_futures()
        """:type : dict[int, list[Future, datetime]]"""

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
            msg_str = msg_str if isinstance(msg_str, str) else msg_str.decode("utf-8")
            msgObj = json.loads(msg_str)
            if "replay" not in msgObj:
                self.__on_replay(client, msg_str, msgObj)
            else:
                self.__on_replayed(msgObj)


        except Exception as e:
            self.on_error(client, e)

    def on_async_message(self, client, message):
        self.message_received_queue.put((message, client))

    def on_closed(self, client):
        """:type client: wshubsapi.ConnectedClient.ConnectedClient"""
        ConnectedClientsHolder.pop_client(client.ID)
        client.api_isClosed = True

    def on_error(self, client, exception):
        log.exception("Error parsing message")

    def replay(self, client, replay, origin_message):
        """
        :type client: wshubsapi.ConnectedClient.ConnectedClient
        :param replay: serialized object to be sent as a replay of a message received
        :param origin_message: Message received (provided for overridden functions)
        """
        client.api_writeMessage(serialize_message(self.pickler, replay))

    def get_new_clients_future(self):
        with self.__new_client_message_id_lock:
            self.__last_client_message_id += 1
            id_ = self.__last_client_message_id
            self.__futures_buffer[id_] = [Future(), datetime.now()]
        return self.__futures_buffer[id_][0], id_

    @Asynchronous.asynchronous()
    def __check_futures(self):
        while True:
            for ID, [_, d] in self.__futures_buffer.items():
                if datetime.now() - d > timedelta(seconds=self.client_function_timeout):
                    self.__on_time_out(ID)
            time.sleep(0.1)

    def __on_time_out(self, id_):
        with self.__new_client_message_id_lock:
            if id_ in self.__futures_buffer:
                future = self.__futures_buffer.pop(id_)[0]
                future.set_exception(HubsApiException("Timeout exception"))

    def __on_replay(self, client, msg_str, msg_obj):
        hub_function = FunctionMessage(msg_obj, client)
        replay = hub_function.call_function()
        if replay is not None:
            self.replay(client, replay, msg_str)

    def __on_replayed(self, msg_obj):
        future = self.__futures_buffer.pop(msg_obj["ID"], [None])[0]
        if future is not None:
            if msg_obj["success"]:
                future.set_result(msg_obj["replay"])
            else:
                future.set_exception(Exception(msg_obj["replay"]))
