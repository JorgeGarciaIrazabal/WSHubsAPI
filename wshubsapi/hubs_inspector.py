import inspect

from wshubsapi import utils
from wshubsapi.client_file_generator.cpp_file_generator import CppFileGenerator
from wshubsapi.client_file_generator.java_file_generator import JAVAFileGenerator
from wshubsapi.client_file_generator.js_file_generator import JSClientFileGenerator
from wshubsapi.client_file_generator.python_file_generator import PythonClientFileGenerator
from wshubsapi.utils import is_function_for_ws_client, get_args, get_defaults


class HubsInspectorError(Exception):
    pass


class HubError(Exception):
    pass


class HubsInspector:
    __hubs_constructed = False
    HUBS_DICT = {}

    def __init__(self):
        raise HubsInspectorError("Static class, do not create an instance of HubsInspector")

    @classmethod
    def __handle_hub_construction_error(cls, e, hub_class):
        if "__init__()" in str(e):
            constructor_with_params_text = "Hubs can't have a constructor with parameters. Check Hub: %s"
            raise HubsInspectorError(constructor_with_params_text % hub_class.__name__)
        else:
            raise e

    @classmethod
    def __construct_hub(cls, hub_class):
        try:
            hub = hub_class()
            hub_name = hub.__class__.__HubName__
            if hub_name in cls.HUBS_DICT:
                raise HubError("Hub's name must be unique, found duplicated name with: {}".format(hub_name))
            if hub_name.startswith("__"):
                raise HubError("Hub's name can not start with '__'")
            if hub_name == "ws_client":
                raise HubError("Hub's name can not be 'wsClient', it is a  reserved name")
            cls.HUBS_DICT[hub_name] = hub
        except TypeError as e:
            cls.__handle_hub_construction_error(e, hub_class)

    @classmethod
    def ignore_hub_implementation(cls, hub_class):
        return "__HubName__" in hub_class.__dict__ and hub_class.__HubName__ is None

    @classmethod
    def get_all_hubs_subclasses(cls, hub_class_to_inspect, current_hub_classes=None):
        current_hub_classes = current_hub_classes if current_hub_classes is not None else []
        for hub_class in hub_class_to_inspect.__subclasses__():
            if not cls.ignore_hub_implementation(hub_class):
                current_hub_classes.append(hub_class)
            else:
                cls.get_all_hubs_subclasses(hub_class, current_hub_classes)
        return current_hub_classes

    @classmethod
    def inspect_implemented_hubs(cls, force_reconstruction=False):
        if not cls.__hubs_constructed or force_reconstruction:
            cls.HUBS_DICT.clear()
            for hub_class in cls.get_all_hubs_subclasses(Hub):
                cls.__construct_hub(hub_class)

            cls.__hubs_constructed = True

    @classmethod
    def construct_js_file(cls, path="."):
        cls.inspect_implemented_hubs()
        JSClientFileGenerator.create_file(path, cls.get_hubs_information())

    @classmethod
    def construct_java_file(cls, package, path="."):
        cls.inspect_implemented_hubs()
        hubs = cls.HUBS_DICT.values()
        JAVAFileGenerator.create_file(path, package, hubs)
        JAVAFileGenerator.create_client_template(path, package, hubs)

    @classmethod
    def construct_python_file(cls, path="."):
        cls.inspect_implemented_hubs()
        PythonClientFileGenerator.create_file(path, cls.HUBS_DICT.values())

    @classmethod
    def construct_cpp_file(cls, path="."):
        cls.inspect_implemented_hubs()
        CppFileGenerator.create_file(path, cls.get_hubs_information())

    @classmethod
    def get_hub_instance(cls, hub):
        """
        :rtype: Hub
        """
        if not isinstance(hub, utils.string_class):
            hub = hub.__HubName__
        return cls.HUBS_DICT[hub]

    @classmethod
    def get_hubs_information(cls):
        info_report = {}
        hubs = cls.HUBS_DICT.values()
        for hub in hubs:
            functions = inspect.getmembers(hub, predicate=is_function_for_ws_client)
            server_methods = {}
            for name, method in functions:
                args_dict = dict(args=get_args(method), defaults=get_defaults(method))
                server_methods[name] = args_dict
            client_methods = {}
            for name, method in hub.client_functions.items():
                args_dict = dict(args=get_args(method), defaults=get_defaults(method))
                client_methods[name] = args_dict

            info_report[hub.__HubName__] = dict(serverMethods=server_methods, clientMethods=client_methods)
        return info_report


from wshubsapi.hub import Hub
