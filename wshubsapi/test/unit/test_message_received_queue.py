# coding=utf-8
import unittest

from flexmock import flexmock

from wshubsapi.comm_environment import CommEnvironment
from wshubsapi.connected_client import ConnectedClient
from wshubsapi.messages_received_queue import MessagesReceivedQueue


class TestWSMessagesReceivedQueue(unittest.TestCase):
    def set_up_queue(self, max_workers):
        self.queue = MessagesReceivedQueue(max_workers)
        return self.queue

    def test_creates__max_workers_workers(self):
        self.queue = self.set_up_queue(3)
        self.queue.executor = flexmock(self.queue.executor)
        self.queue.executor.should_receive("submit").times(3)
        self.queue.start_threads()

    def set_up_infinite_on_message_handler_loop(self, max_workers, message):
        connected_client = flexmock(ConnectedClient(None, None))
        self.queue = self.set_up_queue(max_workers)

        def get_mock():
            self.queue.keepAlive = False
            self.queue.executor.shutdown()
            return [message, connected_client]

        self.queue = flexmock(self.queue)
        self.queue.get = get_mock
        self.queue.executor = flexmock(self.queue.executor, submit=lambda x: x())
        return self.queue, connected_client

    def test_infinite_on_message_handler_loop_calls_client_on_message(self):
        self.queue, cc = self.set_up_infinite_on_message_handler_loop(1, "message")
        self.queue = flexmock(self.queue)
        self.queue.should_receive("on_message").with_args(cc, "message").once()
        self.queue.start_threads()

    def test_infinite_on_message_handler_loop_calls_on_error_if_raises_exception(self):
        self.queue, cc = self.set_up_infinite_on_message_handler_loop(1, "message")
        self.queue = flexmock(self.queue)
        self.queue.should_receive("on_message").and_raise(cc, Exception, "test").once()
        self.queue.should_receive("on_error").with_args(cc, Exception).once()
        self.queue.start_threads()

    def test_infinite_on_message_handler_loop_print_exception_if_connected_client_not_client(self):
        self.queue, cc = self.set_up_infinite_on_message_handler_loop(1, "message")
        self.queue.should_call("get").and_return(["message", None]).once()
        self.queue = flexmock(self.queue)
        self.queue.should_receive("on_message").never()
        self.queue.should_receive("on_error").never()

        self.queue.start_threads()
