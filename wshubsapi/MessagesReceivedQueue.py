try:
    from Queue import Queue
except:
    from queue import Queue

from concurrent.futures import ThreadPoolExecutor


class MessagesReceivedQueue(Queue):
    DEFAULT_MAX_WORKERS = 151

    def __init__(self, comm_environment, max_workers=DEFAULT_MAX_WORKERS):
        """
        :type comm_environment: wshubsapi.CommEnvironment.CommEnvironment
        """
        Queue.__init__(self)
        self.comm_environment = comm_environment
        self.maxWorkers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=self.maxWorkers)
        self.keepAlive = True

    def start_threads(self):
        for i in range(self.maxWorkers):
            self.executor.submit(self.__on_message_handler_loop)

    def __on_message_handler_loop(self):
        while self.keepAlive:
            connected_client = None
            try:
                msg, connected_client = self.get()
                self.comm_environment.on_message(connected_client, msg)
            except Exception as e:
                if connected_client is not None:
                    self.comm_environment.on_error(connected_client, e)
                else:
                    print(str(e))  # todo: create a call back for this exception
