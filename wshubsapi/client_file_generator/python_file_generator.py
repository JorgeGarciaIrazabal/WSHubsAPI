import inspect
import os

from wshubsapi.client_file_generator.client_file_generator import ClientFileGenerator
from wshubsapi.utils import is_function_for_ws_client, get_defaults, get_args

__author__ = 'jgarc'


class PythonClientFileGenerator(ClientFileGenerator):
    TAB = "    "

    @classmethod
    def __get_hub_class_str(cls, hub_name, hub_info):
        func_sep = ("\n" + cls.TAB * 2)
        func_strings = func_sep.join(cls.__get_function_str(hub_name, hub_info))
        return cls.CLASS_TEMPLATE.format(name=hub_name, functions=func_strings)

    @classmethod
    def __get_function_str(cls, hub_name, hub_info):
        func_strings = []
        for method_name, method_info in hub_info["serverMethods"].items():
            args = method_info["args"]
            defaults = method_info["defaults"]
            formatted_args = []
            for i, arg in enumerate(reversed(args)):
                if i >= len(defaults):
                    formatted_args.insert(0, arg)
                else:
                    formatted_args.insert(0, arg + "=" + str(defaults[-i - 1]))
            append_in_args = ("\n" + cls.TAB * 4).join([cls.ARGS_COOK_TEMPLATE.format(name=arg) for arg in args])
            func_strings.append(
                cls.FUNCTION_TEMPLATE.format(name=method_name, args=", ".join(formatted_args), cook=append_in_args))
        return func_strings

    @classmethod
    def __get_attributes_hub(cls, hubs_info):
        return [cls.ATTRIBUTE_HUB_TEMPLATE.format(name=name) for name in hubs_info]

    @classmethod
    def __get_class_strs(cls, hubs_info):
        class_strings = []
        for hub_name, hub_info in hubs_info.items():
            class_strings.append(cls.__get_hub_class_str(hub_name, hub_info))
        return class_strings

    @classmethod
    def create_file(cls, hubs_info, path):
        parent_dir = cls._construct_api_path(path)

        # creating __init__.py if not exist
        __init__file = os.path.join(parent_dir, "__init__.py")
        if not os.path.exists(__init__file):
            with open(os.path.join(parent_dir, "__init__.py"), 'w'):
                pass

        with open(path, "w") as f:
            class_strings = "".join(cls.__get_class_strs(hubs_info))
            attributes_hubs = "\n".join(cls.__get_attributes_hub(hubs_info))
            f.write(cls.WRAPPER.format(Hubs=class_strings, attributesHubs=attributes_hubs))

    WRAPPER = '''import logging
import jsonpickle
import threading
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
            self.log.debug("Connection closed with code:\\n%s\\nAnd reason:\\n%s" % (code, reason))

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
                    client_function = self.api.__getattribute__(msg_obj["hub"]).client.__dict__[msg_obj["function"]]
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
{attributesHubs}

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
{Hubs}'''

    CLASS_TEMPLATE = '''
    class __{name}(object):
        def __init__(self, ws_client, serialization_args):
            hub_name = self.__class__.__name__[2:]
            self.server = self.__Server(ws_client, hub_name, serialization_args)
            self.client = WSSimpleObject()

        class __Server(GenericServer):
            {functions}
'''

    FUNCTION_TEMPLATE = '''
            def {name}(self, {args}):
                """
                :rtype : Future
                """
                args = list()
                {cook}
                id_ = self._get_next_message_id()
                body = {{"hub": self.hub_name, "function": "{name}", "args": args, "ID": id_}}
                future = self.ws_client.get_future(id_)
                send_return_obj = self.ws_client.send(self._serialize_object(body))
                if isinstance(send_return_obj, Future):
                    return send_return_obj
                return future'''

    ARGS_COOK_TEMPLATE = "args.append({name})"

    ATTRIBUTE_HUB_TEMPLATE = "        self.{name} = self.__{name}(self.ws_client, self.serialization_args)"
