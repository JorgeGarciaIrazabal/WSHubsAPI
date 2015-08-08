try:
    from Queue import Queue
except:
    from queue import Queue

import datetime
import inspect
import os
import string
import sys
from inspect import getargspec
import threading
DATE_TIME_FORMAT = '%Y/%m/%d %H:%M:%S %f'

try:
    textTypes = [str, unicode]
except:
    textTypes = [str]
ASCII_UpperCase = string.uppercase if sys.version_info[0] == 2 else string.ascii_uppercase


class classProperty(object):
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
    from wshubsapi.Hub import Hub
    isFunction = lambda x: inspect.ismethod(x) or inspect.isfunction(x)
    functions = inspect.getmembers(Hub, predicate=isFunction)
    functionNames = [f[0] for f in functions ]

    return isFunction(method) and not method.__name__.startswith("_") and method.__name__ not in functionNames

def getModulePath():
    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)
    file = info.filename
    return os.path.dirname(os.path.abspath(file))

class ThreadsPool(list):
    def __init__(self, threadNum=0, setDaemon=True, *args, **kwargs):
        super(ThreadsPool, self).__init__()
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

class WSMessagesReceivedQueue(Queue):
    def __init__(self, threadNum):
        Queue.__init__(self)
        self.threads = ThreadsPool(threadNum, target=self.onMessage, setDaemon=True)

    def startThreads(self):
        self.threads.startAll()

    def onMessage(self):
        while True:
            try:
                msg, connection = self.get()
                connection.onMessage(msg)
            except:
                pass  # todo: create a call back for this exception



from jsonpickle import handlers
def setSerializerDateTimeHandler():
    class WSDateTimeObjects(handlers.BaseHandler):
        def flatten(self, obj, data):
            return obj.strftime(DATE_TIME_FORMAT)

    handlers.register(datetime.datetime, WSDateTimeObjects)
    handlers.register(datetime.date, WSDateTimeObjects)
    handlers.register(datetime.time, WSDateTimeObjects)