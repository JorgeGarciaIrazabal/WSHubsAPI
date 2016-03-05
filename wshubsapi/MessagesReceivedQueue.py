try:
    from Queue import Queue
except:
    from queue import Queue

from concurrent.futures import ThreadPoolExecutor


class MessagesReceivedQueue(Queue):
    DEFAULT_MAX_WORKERS = 151

    def __init__(self, commEnvironment, maxWorkers=DEFAULT_MAX_WORKERS):
        """
        :type commEnvironment: wshubsapi.CommEnvironment.CommEnvironment
        """
        Queue.__init__(self)
        self.commEnvironment = commEnvironment
        self.maxWorkers = maxWorkers
        self.executor = ThreadPoolExecutor(max_workers=self.maxWorkers)
        self.keepAlive = True

    def startThreads(self):
        for i in range(self.DEFAULT_MAX_WORKERS):
            self.executor.submit(self.__infiniteOnMessageHandlerLoop)

    def __infiniteOnMessageHandlerLoop(self):
        while self.keepAlive:
            connectedClient = None
            try:
                msg, connectedClient = self.get()
                self.commEnvironment.onMessage(connectedClient, msg)
            except Exception as e:
                if connectedClient is not None:
                    self.commEnvironment.onError(connectedClient, e)
                else:
                    print(str(e))  # todo: create a call back for this exception