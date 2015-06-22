
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
from datetime import datetime
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

def isNewFunction(method):
    from WSHubsAPI.Hub import Hub
    isFunction = lambda x: inspect.ismethod(x) or inspect.isfunction(x)
    functions = inspect.getmembers(Hub, predicate=isFunction)
    functionNames = [f[0] for f in functions ]

    return isFunction(method) and not method.__name__.startswith("_") and method.__name__ not in functionNames

def getModulePath():
    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)
    file = info.filename
    return os.path.dirname(os.path.abspath(file))

def serializeObject(obj2ser):
    obj = obj2ser if not hasattr(obj2ser, "__dict__") else obj2ser.__dict__
    if isinstance(obj,dict):
        sObj = {}
        for key, value in obj.items():
            if isinstance(value,datetime):
                sObj[key] = value.strftime('%Y/%m/%d %H:%M:%S %f')
            else:
                try:
                    if not key.startswith("_") and id(value) != id(obj2ser):
                        sValue = serializeObject(value)
                        json.dumps(serializeObject(sValue))
                        sObj[key] = sValue
                except TypeError:
                    pass
    elif isinstance(obj,(list,tuple,set)):
        sObj = []
        for value in obj:
            try:
                sValue = serializeObject(value)
                json.dumps(sValue)
                sObj.append(sValue)
            except TypeError:
                pass
    else:
        sObj = obj
    return sObj


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
