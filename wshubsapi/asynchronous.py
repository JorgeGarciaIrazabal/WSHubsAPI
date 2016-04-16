import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

log = logging.getLogger(__name__)
__executor = ThreadPoolExecutor(max_workers=10)


class AsynchronousNotDone(Exception):
    pass


# todo, return a Future object and not a Promise
class Promise(object):
    def __init__(self, future):
        """
        @type future: concurrent.futures._base.Future
        """
        self.result = None
        self.future = future
        self.start_time = datetime.now()

    def is_done(self):
        return self.future.done()

    def get(self, join_timeout=None):
        if join_timeout is not None:
            join_timeout = max([0, join_timeout - (datetime.now() - self.start_time).seconds])
            self.result = self.future.result(join_timeout)
        result = self.future.result(join_timeout)
        if isinstance(result, Exception):
            raise result
        else:
            return result


def asynchronous():
    def real_wrapper(fun):
        def over_function(*args, **kwargs):
            func = kwargs.pop("__func__")
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                log.exception("Error in asynchronous task")
                result = e
            return result

        def wrapper(*args, **kwargs):
            kwargs.update({"__func__": fun})
            future = __executor.submit(over_function, *args, **kwargs)
            result_object = Promise(future)
            kwargs.update({"__ResultObject__": result_object})
            return result_object

        return wrapper

    return real_wrapper
