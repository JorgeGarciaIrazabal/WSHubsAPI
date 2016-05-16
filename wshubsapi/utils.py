import datetime
import inspect
import os
import string
import sys
from inspect import getargspec

import jsonpickle
from jsonpickle import handlers

SENDER_KEY_PARAMETER = "_sender"
DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'
NOT_PASSING_PARAMETERS = (SENDER_KEY_PARAMETER,)
ASCII_UpperCase = string.uppercase if sys.version_info[0] == 2 else string.ascii_uppercase
string_class = basestring if sys.version_info[0] == 2 else (str, bytes)


def get_args(method, include_sender=False):
    args = getargspec(method).args
    if args is None:
        return []
    if hasattr(method, "__self__"):
        args.pop(0)
    if not include_sender:
        for arg in NOT_PASSING_PARAMETERS:
            try:
                args.remove(arg)
            except ValueError:
                pass
    return args


def get_defaults(method):
    defaults = getargspec(method).defaults
    if defaults is None:
        return []
    defaults = list(filter(lambda x: x not in NOT_PASSING_PARAMETERS, list(defaults)))
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


def set_serializer_date_handler():
    class WSDateTimeObjects(handlers.BaseHandler):
        def restore(self, obj):
            pass

        def flatten(self, obj, data):
            return obj.strftime(DATE_TIME_FORMAT)

    handlers.register(datetime.datetime, WSDateTimeObjects)
    handlers.register(datetime.date, WSDateTimeObjects)
    handlers.register(datetime.time, WSDateTimeObjects)


def serialize_message(serialization_args, message):
    serialization_args['unpicklable'] = True
    return jsonpickle.encode(message, **serialization_args)
