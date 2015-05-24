from threading import Thread



class AsynchronousNotDone(Exception):
    pass

class Result(object):
    def __init__(self, thread):
        """
        @type thread: Thread
        """
        self.result = None
        self.thread = thread

    def isDone(self):
        return not self.thread.isAlive()

    def get(self, joinIfNecessary=True):
        if not self.isDone():
            if joinIfNecessary:
                self.thread.join()
            else:
                raise AsynchronousNotDone("Asynchronous not done yet")

        return self.result


def asynchronous(callback=None, callbackArgs=(), callbackKwargs=None):
    if callbackKwargs is None:
        callbackKwargs={}
    def realWrapper(fun, *argss):
        def overFunction(*args,**kwargs):
            func=kwargs.pop("__func__")
            resultObject=kwargs.pop("__ResultObject__")
            result=func(*args,**kwargs)
            resultObject.result=result
            if callback is not None:
                callback(result,*callbackArgs,**callbackKwargs)

        def wrapper(*args, **kwargs):
            kwargs.update({"__func__":fun})
            _mainThread = RThread(overFunction, setDaemon=False)
            resultObject=Result(_mainThread)
            _mainThread.functionsArgs = args
            kwargs.update({"__ResultObject__":resultObject})
            _mainThread.functionKwargs = kwargs
            _mainThread.start()
            return resultObject

        return wrapper
    return realWrapper

"""
#EXAMPLE
def callb(value):
    print "calback"
    print value


@asynchronous(callb)
def timer(delay):
    print "starting"
    time.sleep(delay)
    print "finished"
    return "resultValue"

res=timer(10)
print "waiting timer to finish with value %s"%res.get()
"""

