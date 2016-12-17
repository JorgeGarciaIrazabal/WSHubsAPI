import logging
import jsonpickle
import threading
from wshubsapi import utils
from concurrent.futures import Future

utils.set_serializer_date_handler()
_message_id = 0
_message_lock = threading.RLock()


class GenericClient(object):
    def __setattr__(self, key, value):
        return super(GenericClient, self).__setattr__(key, value)


class GenericServer(object):
    def __init__(self, hub):
        self.hub = hub

    @classmethod
    def _get_next_message_id(cls):
        global _message_id
        with _message_lock:
            _message_id += 1
            return _message_id

    def _serialize_object(self, obj2ser):
        return jsonpickle.encode(obj2ser, **self.hub.serialization_args)

    def construct_message(self, args, function_name):
        id_ = self._get_next_message_id()
        body = {"hub": self.hub.name, "function": function_name, "args": args, "ID": id_}
        future = self.hub.ws_client.get_future(id_)
        send_return_obj = self.hub.ws_client.send(self._serialize_object(body))
        if isinstance(send_return_obj, Future):
            return send_return_obj
        else:
            return future


class GenericBridge(GenericServer):
    def __getattr__(self, function_name):
        def function_wrapper(*args_array):
            """
            :rtype : Future
            """
            args = list()
            args.append(self.clients_ids)
            args.append(function_name)
            args.append(args_array)
            id_ = self._get_next_message_id()
            body = {"hub": self.hub.name, "function": "_client_to_clients_bridge", "args": args, "ID": id_}
            future = self.hub.ws_client.get_future(id_)
            send_return_obj = self.hub.ws_client.send(self._serialize_object(body))
            if isinstance(send_return_obj, Future):
                return send_return_obj
            return future

        return function_wrapper


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
            if "reply" in msg_obj:
                f = self.__futures.get(msg_obj["ID"], None)
                if f is None:
                    return
                if msg_obj["success"]:
                    f.set_result(msg_obj["reply"])
                else:
                    f.set_exception(Exception(msg_obj["reply"]))
            else:
                try:
                    client_function = getattr(getattr(self.api, (msg_obj["hub"])).client, msg_obj["function"])
                    replay_message = dict(ID=msg_obj["ID"])
                    try:
                        reply = client_function(*msg_obj["args"])
                        replay_message["reply"] = reply
                        replay_message["success"] = True
                    except Exception as e:
                        replay_message["reply"] = str(e)
                        replay_message["success"] = False
                    finally:
                        self.api.ws_client.send(self.api.serialize_object(replay_message))
                except:
                    self.log.exception("unable to call client function")

            self.log.debug("Message received: %s" % m.data.decode('utf-8'))

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
        self.SubHub = self.SubHubClass(self.ws_client, self.serialization_args)
        self.UtilsAPIHub = self.UtilsAPIHubClass(self.ws_client, self.serialization_args)
        self.SubHub3 = self.SubHub3Class(self.ws_client, self.serialization_args)
        self.ChatHub = self.ChatHubClass(self.ws_client, self.serialization_args)
        self.SubHub1 = self.SubHub1Class(self.ws_client, self.serialization_args)
        self.EchoHub = self.EchoHubClass(self.ws_client, self.serialization_args)
        self.SubHub2 = self.SubHub2Class(self.ws_client, self.serialization_args)

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

    class SubHubClass(object):
        def __init__(self, ws_client, serialization_args):
            self.name = "SubHub"
            self.ws_client = ws_client
            self.serialization_args = serialization_args
            self.server = self.ServerClass(self)
            self.client = self.ClientClass()

        def get_clients(self, client_ids):
            return HubsAPI.SubHubClass.ClientsInServer(client_ids, self)

        class ServerClass(GenericServer):
            
            def subscribe_to_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "subscribe_to_hub")

            def unsubscribe_from_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "unsubscribe_from_hub")

            def get_subscribed_clients_ids(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "get_subscribed_clients_ids")

        class ClientClass(GenericClient):
            def __init__(self):
                pass
            

        class ClientsInServer(GenericBridge):
            def __init__(self, client_ids, hub):
                super(self.__class__, self).__init__(hub)
                self.clients_ids = client_ids
            

    class UtilsAPIHubClass(object):
        def __init__(self, ws_client, serialization_args):
            self.name = "UtilsAPIHub"
            self.ws_client = ws_client
            self.serialization_args = serialization_args
            self.server = self.ServerClass(self)
            self.client = self.ClientClass()

        def get_clients(self, client_ids):
            return HubsAPI.UtilsAPIHubClass.ClientsInServer(client_ids, self)

        class ServerClass(GenericServer):
            
            def unsubscribe_from_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "unsubscribe_from_hub")

            def subscribe_to_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "subscribe_to_hub")

            def get_hubs_structure(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "get_hubs_structure")

            def get_id(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "get_id")

            def get_subscribed_clients_ids(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "get_subscribed_clients_ids")

            def set_id(self, client_id):
                """
                :rtype : Future
                """
                args = list()
                args.append(client_id)
                return self.construct_message(args, "set_id")

            def is_client_connected(self, client_id):
                """
                :rtype : Future
                """
                args = list()
                args.append(client_id)
                return self.construct_message(args, "is_client_connected")

        class ClientClass(GenericClient):
            def __init__(self):
                pass
            

        class ClientsInServer(GenericBridge):
            def __init__(self, client_ids, hub):
                super(self.__class__, self).__init__(hub)
                self.clients_ids = client_ids
            

    class SubHub3Class(object):
        def __init__(self, ws_client, serialization_args):
            self.name = "SubHub3"
            self.ws_client = ws_client
            self.serialization_args = serialization_args
            self.server = self.ServerClass(self)
            self.client = self.ClientClass()

        def get_clients(self, client_ids):
            return HubsAPI.SubHub3Class.ClientsInServer(client_ids, self)

        class ServerClass(GenericServer):
            
            def subscribe_to_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "subscribe_to_hub")

            def unsubscribe_from_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "unsubscribe_from_hub")

            def get_subscribed_clients_ids(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "get_subscribed_clients_ids")

        class ClientClass(GenericClient):
            def __init__(self):
                pass
            

        class ClientsInServer(GenericBridge):
            def __init__(self, client_ids, hub):
                super(self.__class__, self).__init__(hub)
                self.clients_ids = client_ids
            

    class ChatHubClass(object):
        def __init__(self, ws_client, serialization_args):
            self.name = "ChatHub"
            self.ws_client = ws_client
            self.serialization_args = serialization_args
            self.server = self.ServerClass(self)
            self.client = self.ClientClass()

        def get_clients(self, client_ids):
            return HubsAPI.ChatHubClass.ClientsInServer(client_ids, self)

        class ServerClass(GenericServer):
            
            def unsubscribe_from_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "unsubscribe_from_hub")

            def subscribe_to_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "subscribe_to_hub")

            def send_to_all(self, name, message="hello"):
                """
                :rtype : Future
                """
                args = list()
                args.append(name)
                args.append(message)
                return self.construct_message(args, "send_to_all")

            def get_subscribed_clients_ids(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "get_subscribed_clients_ids")

            def send_message_to_client(self, message, client_id):
                """
                :rtype : Future
                """
                args = list()
                args.append(message)
                args.append(client_id)
                return self.construct_message(args, "send_message_to_client")

            def raise_exception(self, exception_message):
                """
                :rtype : Future
                """
                args = list()
                args.append(exception_message)
                return self.construct_message(args, "raise_exception")

        class ClientClass(GenericClient):
            def __init__(self):
                pass
            

        class ClientsInServer(GenericBridge):
            def __init__(self, client_ids, hub):
                super(self.__class__, self).__init__(hub)
                self.clients_ids = client_ids
            

    class SubHub1Class(object):
        def __init__(self, ws_client, serialization_args):
            self.name = "SubHub1"
            self.ws_client = ws_client
            self.serialization_args = serialization_args
            self.server = self.ServerClass(self)
            self.client = self.ClientClass()

        def get_clients(self, client_ids):
            return HubsAPI.SubHub1Class.ClientsInServer(client_ids, self)

        class ServerClass(GenericServer):
            
            def subscribe_to_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "subscribe_to_hub")

            def unsubscribe_from_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "unsubscribe_from_hub")

            def get_subscribed_clients_ids(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "get_subscribed_clients_ids")

        class ClientClass(GenericClient):
            def __init__(self):
                pass
            

        class ClientsInServer(GenericBridge):
            def __init__(self, client_ids, hub):
                super(self.__class__, self).__init__(hub)
                self.clients_ids = client_ids
            

    class EchoHubClass(object):
        def __init__(self, ws_client, serialization_args):
            self.name = "EchoHub"
            self.ws_client = ws_client
            self.serialization_args = serialization_args
            self.server = self.ServerClass(self)
            self.client = self.ClientClass()

        def get_clients(self, client_ids):
            return HubsAPI.EchoHubClass.ClientsInServer(client_ids, self)

        class ServerClass(GenericServer):
            
            def subscribe_to_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "subscribe_to_hub")

            def unsubscribe_from_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "unsubscribe_from_hub")

            def get_subscribed_clients_ids(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "get_subscribed_clients_ids")

            def echo(self, message):
                """
                :rtype : Future
                """
                args = list()
                args.append(message)
                return self.construct_message(args, "echo")

            def echo_to_sender(self, message):
                """
                :rtype : Future
                """
                args = list()
                args.append(message)
                return self.construct_message(args, "echo_to_sender")

        class ClientClass(GenericClient):
            def __init__(self):
                pass
            

        class ClientsInServer(GenericBridge):
            def __init__(self, client_ids, hub):
                super(self.__class__, self).__init__(hub)
                self.clients_ids = client_ids
            

    class SubHub2Class(object):
        def __init__(self, ws_client, serialization_args):
            self.name = "SubHub2"
            self.ws_client = ws_client
            self.serialization_args = serialization_args
            self.server = self.ServerClass(self)
            self.client = self.ClientClass()

        def get_clients(self, client_ids):
            return HubsAPI.SubHub2Class.ClientsInServer(client_ids, self)

        class ServerClass(GenericServer):
            
            def subscribe_to_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "subscribe_to_hub")

            def unsubscribe_from_hub(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "unsubscribe_from_hub")

            def get_subscribed_clients_ids(self, ):
                """
                :rtype : Future
                """
                args = list()
                
                return self.construct_message(args, "get_subscribed_clients_ids")

        class ClientClass(GenericClient):
            def __init__(self):
                pass
            

        class ClientsInServer(GenericBridge):
            def __init__(self, client_ids, hub):
                super(self.__class__, self).__init__(hub)
                self.clients_ids = client_ids
            
