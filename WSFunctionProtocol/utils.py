try:
    from Queue import Queue
except:
    from queue import Queue
from collections import OrderedDict
import inspect
import json
import logging
import os
import string
import sys
from inspect import getargspec
import threading

try:
    textTypes = [str, unicode]
except:
    textTypes = [str]
ASCII_UpperCase = string.uppercase if sys.version_info[0] == 2 else string.ascii_uppercase


class classproperty(object):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)

def getArgs(method):
    args = getargspec(method).args
    if args is None: return []
    for arg in ("self",):
        try:
            args.remove(arg)
        except:
            pass
    return args

def getDefaults(method):
    d = getargspec(method).defaults
    if d is None: return []
    d = list(d)
    for i in range(len(d)):
        if isinstance(d[i], tuple(textTypes)):  # todo: check with python 3
            d[i] = '"%s"' % d[i]
    return d

def isPublicFunction(method):
    isFunction = lambda x: inspect.ismethod(x) or inspect.isfunction(x)
    return isFunction(method) and not method.__name__.startswith("_")

def getModulePath():
    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)
    file = info.filename
    return os.path.dirname(os.path.abspath(file))



FUNCTION_MESSAGE = """Function "%s" called.
    Parameters used: %s
    Result: %s
"""
strBasicObjects = textTypes if sys.version_info[0] == 2 else [str]
basicObjectList = [list, dict, str, int, float, bool, type(None)]
basicObjectList.extend(strBasicObjects)
MAX_STRING_LENGTH = 400

log = logging.getLogger(__name__)

class LogFunction:
    @staticmethod
    def debug(func):
        return LogFunction.__log(func, log.debug)

    @staticmethod
    def info(func):
        return LogFunction.__log(func, log.info)

    @staticmethod
    def warning(func):
        return LogFunction.__log(func, log.warning)

    @staticmethod
    def error(func):
        return LogFunction.__log(func, log.error)

    @staticmethod
    def critical(func):
        return LogFunction.__log(func, log.critical)

    @staticmethod
    def __log(func, logFunc):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            parameters = OrderedDict()
            specs = getargspec(func)
            argsName = specs[0]
            for i, arg in enumerate(args):
                if i >= len(argsName):
                    parameters["args"] = str(args[i:])
                else:
                    if isinstance(args[i], basicObjectList):
                        parameters[argsName[i]] = args[i]
                    else:
                        parameters[argsName[i]] = str(args[i])
            for key, value in kwargs.items():
                if isinstance(value, basicObjectList):
                    parameters[key] = value
                else:
                    parameters[key] = str(value)

            if not isinstance(result, basicObjectList):
                result = str(result)

            try:
                parameters.pop("self")
            except:
                pass
            parameters = json.dumps(parameters, separators=(',', ' = '))
            if len(parameters) >= MAX_STRING_LENGTH: parameters = parameters[:MAX_STRING_LENGTH - 3] + "..."
            if isinstance(result, strBasicObjects) and len(result) >= MAX_STRING_LENGTH:
                result = result[:MAX_STRING_LENGTH - 3] + "..."
            logFunc(FUNCTION_MESSAGE % (func.__name__, parameters, result))
            return result

        return wrapper

class ThreadsList(list):
    def __init__(self, threadNum=0, setDaemon=True, *args, **kwargs):
        super(ThreadsList, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self.setDaemon = setDaemon
        for i in range(threadNum):
            self.append(threading.Thread(*args, **kwargs))
            self[-1].setDaemon(setDaemon)

    def joinAll(self, **kwargs):
        auxThreads = []

        def joinThread(thread, **kwargs):
            thread.join(**kwargs)

        def joinThreads(**kwargs):
            for thread in self:
                auxThreads.append(threading.Thread(joinThread, (thread,)))
                auxThreads[-1].start()
            for thread in auxThreads:
                thread.join()

        t = threading.Thread(target=joinThreads, **kwargs)
        t.start()
        t.join()

    def startAll(self):
        for t in self:
            t.start()

    def isAnyAlive(self):
        for t in self:
            if t.isAlive(): return True

    def addAndStartThread(self, n=1):
        for i in range(n):
            self.append(threading.Thread(*self.args, **self.kwargs))
            self[-1].setDaemon(self.setDaemon)
            self[-1].start()

class WSThreadsQueue(Queue):
    def __init__(self, threadNum):
        Queue.__init__(self)
        self.threads = ThreadsList(threadNum, target=self.onMessage, setDaemon=True)
        self.threads.startAll()

    def onMessage(self):
        while True:
            try:
                msg, connection = self.get()
                connection.onMessage(msg)
            except:
                pass  # todo: create a call back for this exception
