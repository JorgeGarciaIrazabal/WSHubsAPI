import inspect

from wshubsapi.ClientFileGenerator.CppFileGenerator import CppFileGenerator
from wshubsapi.ClientFileGenerator.JAVAFileGenerator import JAVAFileGenerator
from wshubsapi.ClientFileGenerator.JSClientFileGenerator import JSClientFileGenerator
from wshubsapi.ClientFileGenerator.PythonClientFileGenerator import PythonClientFileGenerator
from wshubsapi.utils import is_function_for_ws_client, get_args, get_defaults


class HubsInspectorError(Exception):
    pass


class HubsInspector:
    __hubs_constructed = False
    HUBs_DICT = {}

    def __init__(self):
        raise HubsInspectorError("Static class, do not create an instance of HubsInspector")

    @classmethod
    def ignore_hub_implementation(cls, hub_class):
        return "__HubName__" in hub_class.__dict__ and hub_class.__HubName__ is None

    @classmethod
    def get_all_hubs_subclasses(cls, hub_class_to_inspect, current_hub_classes=None):
        current_hub_classes = current_hub_classes if current_hub_classes is not None else []
        for hubClass in hub_class_to_inspect.__subclasses__():
            if not cls.ignore_hub_implementation(hubClass):
                current_hub_classes.append(hubClass)
            else:
                cls.get_all_hubs_subclasses(hubClass, current_hub_classes)
        return current_hub_classes

    @classmethod
    def inspect_implemented_hubs(cls, force_reconstruction=False):
        if not cls.__hubs_constructed or force_reconstruction:
            cls.HUBs_DICT.clear()
            for hub_class in cls.get_all_hubs_subclasses(Hub):
                try:
                    hub_class()
                except TypeError as e:
                    if "__init__()" in str(e):
                        raise HubsInspectorError(
                            "Hubs can't have a constructor with parameters. Check Hub: %s" % hub_class.__name__)
                    else:
                        raise e
            cls.__hubs_constructed = True

    @classmethod
    def construct_js_file(cls, path="."):
        cls.inspect_implemented_hubs()
        JSClientFileGenerator.create_file(path, cls.get_hubs_information())

    @classmethod
    def construct_java_file(cls, package, path="."):
        cls.inspect_implemented_hubs()
        hubs = cls.HUBs_DICT.values()
        JAVAFileGenerator.create_file(path, package, hubs)
        JAVAFileGenerator.create_client_template(path, package, hubs)

    @classmethod
    def construct_python_file(cls, path="."):
        cls.inspect_implemented_hubs()
        PythonClientFileGenerator.create_file(path, cls.HUBs_DICT.values())

    @classmethod
    def construct_cpp_file(cls, path="."):
        cls.inspect_implemented_hubs()
        CppFileGenerator.create_file(path, cls.get_hubs_information())

    @classmethod
    def get_hub_instance(cls, hub):
        """
        :rtype: Hub
        """
        if not isinstance(hub, basestring):
            hub = hub.__HubName__
        return cls.HUBs_DICT[hub]

    @classmethod
    def get_hubs_information(cls):
        info_report = {}
        hubs = cls.HUBs_DICT.values()
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


from wshubsapi.Hub import Hub
