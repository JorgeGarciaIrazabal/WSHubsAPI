import inspect
import os
import string
from collections import OrderedDict

SENDER_KEY_PARAMETER = "_sender"
DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'
NOT_PASSING_PARAMETERS = (SENDER_KEY_PARAMETER,)
ASCII_UpperCase = string.ascii_uppercase
string_class = (str, bytes)


def get_args(method, include_sender=False):
    args = OrderedDict(inspect.signature(method).parameters)
    if not include_sender:
        for arg in NOT_PASSING_PARAMETERS:
            args.pop(arg, None)
    return list(args.keys())


def get_defaults(method):
    defaults = []
    for param in inspect.signature(method).parameters.values():
        if param.default is not param.empty:
            defaults.append(param.default)

    defaults = list(filter(lambda x: x not in NOT_PASSING_PARAMETERS, defaults))
    for i, default_value in enumerate(defaults):
        if isinstance(defaults[i], string_class):
            defaults[i] = '"%s"' % default_value
    return defaults


def is_function_for_ws_client(method):
    def is_function():
        return inspect.ismethod(method) or inspect.isfunction(method)

    return is_function() and not method.__name__.startswith("_") and method.__name__


def get_module_path():
    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)
    file_name = info.filename
    return os.path.dirname(os.path.abspath(file_name))

