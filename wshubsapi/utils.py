import jsonpickle
import datetime
import inspect
import os
import string
import sys
from inspect import getargspec
from jsonpickle import handlers

SENDER_KEY_PARAMETER = "_sender"
DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'
NOT_PASSING_PARAMETERS = (SENDER_KEY_PARAMETER,)

ASCII_UpperCase = string.uppercase if sys.version_info[0] == 2 else string.ascii_uppercase


def getArgs(method, includeSender=False):
    args = getargspec(method).args
    if args is None: return []
    if hasattr(method, "__self__"):
        args.pop(0)
    if not includeSender:
        for arg in NOT_PASSING_PARAMETERS:
            try:
                args.remove(arg)
            except:
                pass
    return args


def getDefaults(method):
    defaults = getargspec(method).defaults
    if defaults is None: return []
    defaults = list(filter(lambda x: x not in NOT_PASSING_PARAMETERS, list(defaults)))
    for i, dValue in enumerate(defaults):
        if isinstance(defaults[i], basestring):
            defaults[i] = '"%s"' % dValue
    return defaults


def isFunctionForWSClient(method):
    from wshubsapi.Hub import Hub
    isFunction = lambda x: inspect.ismethod(x) or inspect.isfunction(x)
    BaseHubFunctions = inspect.getmembers(Hub, predicate=isFunction)
    BaseHubFunctionsNames = [f[0] for f in BaseHubFunctions]

    return isFunction(method) and not method.__name__.startswith("_") and method.__name__


def getModulePath():
    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)
    fileName = info.filename
    return os.path.dirname(os.path.abspath(fileName))


def setSerializerDateTimeHandler():
    class WSDateTimeObjects(handlers.BaseHandler):
        def restore(self, obj):
            pass

        def flatten(self, obj, data):
            return obj.strftime(DATE_TIME_FORMAT)

    handlers.register(datetime.datetime, WSDateTimeObjects)
    handlers.register(datetime.date, WSDateTimeObjects)
    handlers.register(datetime.time, WSDateTimeObjects)


def serializeMessage(serializationPickler, message):
    return jsonpickle.encode(serializationPickler.flatten(message))


class MessageSeparator:
    DEFAULT_API_SEP = "*API_SEP*"

    def __init__(self, messageSeparator=DEFAULT_API_SEP):
        self.buffer = ""
        self.sep = messageSeparator

    def addData(self, data):
        data = self.buffer + data
        messages = data.split(self.sep)
        self.buffer = messages.pop(-1)
        return messages
