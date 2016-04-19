# coding=utf-8
import time
import unittest

from flexmock import flexmock, flexmock_teardown

from wshubsapi.comm_environment import CommEnvironment
from wshubsapi.connected_client import ConnectedClient
from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.messages_received_queue import MessagesReceivedQueue
from wshubsapi.utils import *


class TestUtils(unittest.TestCase):
    def setUp(self):
        flexmock(MessagesReceivedQueue, DEFAULT_MAX_WORKERS=0)
        self.queue = None

    def tearDown(self):
        flexmock_teardown()
        if isinstance(self.queue, MessagesReceivedQueue):
            self.queue.keepAlive = False
            for i in range(self.queue.maxWorkers):
                self.queue.put(None, None)
            self.queue.executor.shutdown()

    def test_ASCII_UpperCaseIsInitialized(self):
        random_letters = ["A", "Q", "P"]
        for letter in random_letters:
            self.assertIn(letter, ASCII_UpperCase, "letter in ASCII_UpperCase")

    def test_ASCII_UpperCaseDoesNotContainNotASCIICharacters(self):
        non_ascii_letter = "Ñ"
        self.assertNotIn(non_ascii_letter, ASCII_UpperCase)

    def test_getArgsReturnsAllArgumentsInMethod(self):
        class AuxClass:
            def auxFunc(self, x, y, z):
                pass

            @staticmethod
            def auxStatic(self, x, y):
                pass

            @classmethod
            def auxClassMethod(cls, x, y):
                pass

        testCases = [
            {"method": lambda x, y, z: x, "expected": ["x", "y", "z"]},
            {"method": lambda y=2, z=1: y, "expected": ["y", "z"]},
            {"method": lambda: 1, "expected": []},
            {"method": AuxClass().auxFunc, "expected": ["x", "y", "z"]},
            {"method": AuxClass.auxStatic, "expected": ["self", "x", "y"]},
            {"method": AuxClass.auxClassMethod, "expected": ["x", "y"]}
        ]
        for case in testCases:
            returnedFromFunction = get_args(case["method"])

            self.assertEqual(returnedFromFunction, case["expected"])

    def test_getDefaultsReturnsTheDefaultValues(self):
        testCases = [
            {"method": lambda x, y, z: x, "expected": []},
            {"method": lambda y=2, z="a": y, "expected": [2, '"a"']},
            {"method": lambda x, y=4, z="ñoño": 1, "expected": [4, '"ñoño"']},
        ]
        for case in testCases:
            returnedFromFunction = get_defaults(case["method"])

            self.assertEqual(returnedFromFunction, case["expected"])

    def test_isFunctionForWSClient_IncludesStandardFunction(self):
        def thisIsANewFunction(test):
            print(test)

        self.assertTrue(is_function_for_ws_client(thisIsANewFunction), "new function is detected")

    def test_isFunctionForWSClient_ExcludesProtectedAndPrivateFunctions(self):
        def _thisIsAProtectedFunction(test):
            print(test)

        def __thisIsAPrivateFunction(test):
            print(test)

        self.assertFalse(is_function_for_ws_client(_thisIsAProtectedFunction), "protected function is excluded")
        self.assertFalse(is_function_for_ws_client(__thisIsAPrivateFunction), "private function is excluded")

    def test_isFunctionForWSClient_ExcludesAlreadyExistingFunctions(self):
        self.assertFalse(is_function_for_ws_client(HubsInspector.HUBS_DICT), "excludes existing functions")

    def test_getModulePath_ReturnsTestUtilsPyModulePath(self):
        self.assertIn("wshubsapi" + os.sep + "test", get_module_path())

    def setUp_WSMessagesReceivedQueue(self, comm_environment, max_workers):
        self.queue = MessagesReceivedQueue(comm_environment, max_workers)
        return self.queue

    def test_WSMessagesReceivedQueue_Creates__MAX_WORKERS__WORKERS(self):
        self.queue = self.setUp_WSMessagesReceivedQueue(CommEnvironment(max_workers=0), 3)
        self.queue.executor = flexmock(self.queue.executor)
        self.queue.executor.should_receive("submit").times(3)
        self.queue.start_threads()

    def setUp_WSMessagesReceivedQueue_infiniteOnMessageHandlerLoop(self, max_workers, message):
        comm_environment = flexmock(CommEnvironment(max_workers=0))
        connected_client = flexmock(ConnectedClient(comm_environment, None))
        self.queue = self.setUp_WSMessagesReceivedQueue(comm_environment, max_workers)

        def get_mock():
            self.queue.keepAlive = False
            return [message, connected_client]

        self.queue = flexmock(self.queue)
        self.queue.get = get_mock
        self.queue.executor = flexmock(self.queue.executor, submit=lambda x: x())
        return self.queue, connected_client, comm_environment

    def test_WSMessagesReceivedQueue_infiniteOnMessageHandlerLoop_CallsClientOnMessage(self):
        self.queue, cc, commEnvironment = self.setUp_WSMessagesReceivedQueue_infiniteOnMessageHandlerLoop(1, "message")
        commEnvironment.should_receive("on_message").with_args(cc, "message").once()
        self.queue.start_threads()

    def test_WSMessagesReceivedQueue_infiniteOnMessageHandlerLoop_CallsOnErrorIfRaisesException(self):
        self.queue, cc, commEnvironment = self.setUp_WSMessagesReceivedQueue_infiniteOnMessageHandlerLoop(1, "message")
        commEnvironment.should_receive("on_message").and_raise(cc, Exception, "test").once()
        commEnvironment.should_receive("on_error").with_args(cc, Exception).once()
        self.queue.start_threads()

    def test_WSMessagesReceivedQueue_infiniteOnMessageHandlerLoop_PrintExceptionIfConnectedClientIsNoConnectedClient(
            self):
        self.queue, cc, comm_environment = self.setUp_WSMessagesReceivedQueue_infiniteOnMessageHandlerLoop(1, "message")
        self.queue.should_call("get").and_return(["message", None]).once()
        comm_environment.should_receive("on_message").never()
        comm_environment.should_receive("on_error").never()

        self.queue.start_threads()
