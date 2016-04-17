import json
import logging
import threading
import jsonpickle
from jsonpickle.pickler import Pickler
from wshubsapi import utils
from concurrent.futures import Future

utils.set_serializer_date_handler()


class WSSimpleObject(object):
    def __setattr__(self, key, value):
        return super(WSSimpleObject, self).__setattr__(key, value)


class GenericServer(object):
    __message_id = 0
    __message_lock = threading.RLock()

    def __init__(self, ws_client, hub_name, serialization_args):
        """
        :type ws_client: WSHubsAPIClient
        """
        self.ws_client = ws_client
        self.hub_name = hub_name
        self.serialization_args = serialization_args

    @classmethod
    def _get_next_message_id(cls):
        with cls.__message_lock:
            cls.__message_id += 1
            return cls.__message_id

    def _serialize_object(self, obj2ser):
        return jsonpickle.encode(obj2ser, **self.serialization_args)


def construct_api_client_class(client_class):
    if client_class is None:
        from ws4py.client.threadedclient import WebSocketClient
        client_class = WebSocketClient

    class WSHubsAPIClient(client_class):
        def __init__(self, api, url):
            """
            :type api: HubsAPI
            """
            client_class.__init__(self, url)
            self.__futures = dict()
            self.is_opened = False
            self.api = api
            self.log = logging.getLogger(__name__)
            self.log.addHandler(logging.NullHandler())

        def opened(self):
            self.is_opened = True
            self.log.debug("Connection opened")

        def closed(self, code, reason=None):
            self.log.debug("Connection closed with code:\n%s\nAnd reason:\n%s" % (code, reason))

        def received_message(self, m):
            try:
                msg_obj = jsonpickle.decode(m.data.decode('utf-8'))
            except Exception as e:
                self.on_error(e)
                return
            if "replay" in msg_obj:
                f = self.__futures.get(msg_obj["ID"], None)
                if f is None:
                    return
                if msg_obj["success"]:
                    f.set_result(msg_obj["replay"])
                else:
                    f.set_exception(Exception(msg_obj["replay"]))
            else:
                try:
                    client_function = self.api.__getattribute__(msg_obj["hub"]).client.__dict__[msg_obj["function"]]
                    replay_message = dict(ID=msg_obj["ID"])
                    try:
                        replay = client_function(*msg_obj["args"])
                        replay_message["replay"] = replay
                        replay_message["success"] = True
                    except Exception as e:
                        replay_message["replay"] = str(e)
                        replay_message["success"] = False
                    finally:
                        self.api.ws_client.send(self.api.serialize_object(replay_message))
                except:
                    pass

            self.log.debug("Received message: %s" % m.data.decode('utf-8'))

        def get_future(self, id_):
            """
            :rtype : Future
            """
            self.__futures[id_] = Future()
            return self.__futures[id_]

        def on_error(self, exception):
            self.log.exception("Error in protocol")

        def default_on_error(self, error):
            pass

    return WSHubsAPIClient


class HubsAPI(object):
    def __init__(self, url, client_class=None, serialization_max_depth=5, serialization_max_iter=100):
        api_client_class = construct_api_client_class(client_class)
        self.ws_client = api_client_class(self, url)
        self.ws_client.default_on_error = lambda error: None
        self.serialization_args = dict(max_depth=serialization_max_depth, max_iter=serialization_max_iter)
        self.serialization_args['unpicklable'] = True
        self.ChatHub = self.__ChatHub(self.ws_client, self.serialization_args)
        self.UtilsAPIHub = self.__UtilsAPIHub(self.ws_client, self.serialization_args)

    @property
    def default_on_error(self):
        return None

    @default_on_error.setter
    def default_on_error(self, func):
        self.ws_client.default_on_error = func

    def connect(self):
        self.ws_client.connect()

    def serialize_object(self, obj2ser):
        return jsonpickle.encode(obj2ser, self.serialization_args)

    class __ChatHub(object):
        def __init__(self, ws_client, serialization_args):
            hub_name = self.__class__.__name__[2:]
            self.server = self.__Server(ws_client, hub_name, serialization_args)
            self.client = WSSimpleObject()

        class __Server(GenericServer):
            
            def class_method(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                id_ = self._get_next_message_id()
                body = {"hub": self.hub_name, "function": "class_method", "args": args, "ID": id_}
                future = self.ws_client.get_future(id_)
                send_return_obj = self.ws_client.send(self._serialize_object(body))
                if isinstance(send_return_obj, Future):
                    return send_return_obj
                return future
        
            def get_subscribed_clients_to_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                id_ = self._get_next_message_id()
                body = {"hub": self.hub_name, "function": "get_subscribed_clients_to_hub", "args": args, "ID": id_}
                future = self.ws_client.get_future(id_)
                send_return_obj = self.ws_client.send(self._serialize_object(body))
                if isinstance(send_return_obj, Future):
                    return send_return_obj
                return future
        
            def send_to_all(self, name, message="hello"):
                """
                :rtype : Future
                """
                args = list()
                args.append(name)
                args.append(message)
                id_ = self._get_next_message_id()
                body = {"hub": self.hub_name, "function": "send_to_all", "args": args, "ID": id_}
                future = self.ws_client.get_future(id_)
                send_return_obj = self.ws_client.send(self._serialize_object(body))
                if isinstance(send_return_obj, Future):
                    return send_return_obj
                return future
        
            def static_func(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                id_ = self._get_next_message_id()
                body = {"hub": self.hub_name, "function": "static_func", "args": args, "ID": id_}
                future = self.ws_client.get_future(id_)
                send_return_obj = self.ws_client.send(self._serialize_object(body))
                if isinstance(send_return_obj, Future):
                    return send_return_obj
                return future
        
            def subscribe_to_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                id_ = self._get_next_message_id()
                body = {"hub": self.hub_name, "function": "subscribe_to_hub", "args": args, "ID": id_}
                future = self.ws_client.get_future(id_)
                send_return_obj = self.ws_client.send(self._serialize_object(body))
                if isinstance(send_return_obj, Future):
                    return send_return_obj
                return future
        
            def unsubscribe_from_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                id_ = self._get_next_message_id()
                body = {"hub": self.hub_name, "function": "unsubscribe_from_hub", "args": args, "ID": id_}
                future = self.ws_client.get_future(id_)
                send_return_obj = self.ws_client.send(self._serialize_object(body))
                if isinstance(send_return_obj, Future):
                    return send_return_obj
                return future

    class __UtilsAPIHub(object):
        def __init__(self, ws_client, serialization_args):
            hub_name = self.__class__.__name__[2:]
            self.server = self.__Server(ws_client, hub_name, serialization_args)
            self.client = WSSimpleObject()

        class __Server(GenericServer):
            
            def get_hubs_structure(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                id_ = self._get_next_message_id()
                body = {"hub": self.hub_name, "function": "get_hubs_structure", "args": args, "ID": id_}
                future = self.ws_client.get_future(id_)
                send_return_obj = self.ws_client.send(self._serialize_object(body))
                if isinstance(send_return_obj, Future):
                    return send_return_obj
                return future
        
            def get_id(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                id_ = self._get_next_message_id()
                body = {"hub": self.hub_name, "function": "get_id", "args": args, "ID": id_}
                future = self.ws_client.get_future(id_)
                send_return_obj = self.ws_client.send(self._serialize_object(body))
                if isinstance(send_return_obj, Future):
                    return send_return_obj
                return future
        
            def get_subscribed_clients_to_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                id_ = self._get_next_message_id()
                body = {"hub": self.hub_name, "function": "get_subscribed_clients_to_hub", "args": args, "ID": id_}
                future = self.ws_client.get_future(id_)
                send_return_obj = self.ws_client.send(self._serialize_object(body))
                if isinstance(send_return_obj, Future):
                    return send_return_obj
                return future
        
            def is_client_connected(self, client_id):
                """
                :rtype : Future
                """
                args = list()
                args.append(client_id)
                id_ = self._get_next_message_id()
                body = {"hub": self.hub_name, "function": "is_client_connected", "args": args, "ID": id_}
                future = self.ws_client.get_future(id_)
                send_return_obj = self.ws_client.send(self._serialize_object(body))
                if isinstance(send_return_obj, Future):
                    return send_return_obj
                return future
        
            def set_id(self, client_id):
                """
                :rtype : Future
                """
                args = list()
                args.append(client_id)
                id_ = self._get_next_message_id()
                body = {"hub": self.hub_name, "function": "set_id", "args": args, "ID": id_}
                future = self.ws_client.get_future(id_)
                send_return_obj = self.ws_client.send(self._serialize_object(body))
                if isinstance(send_return_obj, Future):
                    return send_return_obj
                return future
        
            def subscribe_to_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                id_ = self._get_next_message_id()
                body = {"hub": self.hub_name, "function": "subscribe_to_hub", "args": args, "ID": id_}
                future = self.ws_client.get_future(id_)
                send_return_obj = self.ws_client.send(self._serialize_object(body))
                if isinstance(send_return_obj, Future):
                    return send_return_obj
                return future
        
            def unsubscribe_from_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                id_ = self._get_next_message_id()
                body = {"hub": self.hub_name, "function": "unsubscribe_from_hub", "args": args, "ID": id_}
                future = self.ws_client.get_future(id_)
                send_return_obj = self.ws_client.send(self._serialize_object(body))
                if isinstance(send_return_obj, Future):
                    return send_return_obj
                return future
