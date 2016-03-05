# coding=utf-8
import time
import unittest

from flexmock import flexmock

from wshubsapi.CommEnvironment import CommEnvironment
from wshubsapi.ConnectedClient import ConnectedClient
from wshubsapi.HubsInspector import HubsInspector
from wshubsapi.MessagesReceivedQueue import MessagesReceivedQueue
from wshubsapi.utils import *


class TestUtils(unittest.TestCase):

    def test_ASCII_UpperCaseIsInitialized(self):
        randomExistingLetters = ["A", "Q", "P"]
        for letter in randomExistingLetters:
            self.assertIn(letter, ASCII_UpperCase, "letter in ASCII_UpperCase")

    def test_ASCII_UpperCaseDoesNotContainNotASCIICharacters(self):
        nonASCII_letter = "Ñ"
        self.assertNotIn(nonASCII_letter, ASCII_UpperCase)

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
            returnedFromFunction = getArgs(case["method"])

            self.assertEqual(returnedFromFunction, case["expected"])

    def test_getDefaultsReturnsTheDefaultValues(self):
        testCases = [
            {"method": lambda x, y, z: x, "expected": []},
            {"method": lambda y=2, z="a": y, "expected": [2, '"a"']},
            {"method": lambda x, y=4, z="ñoño": 1, "expected": [4, '"ñoño"']},
        ]
        for case in testCases:
            returnedFromFunction = getDefaults(case["method"])

            self.assertEqual(returnedFromFunction, case["expected"])

    def test_isFunctionForWSClient_IncludesStandardFunction(self):
        def thisIsANewFunction(test):
            print(test)

        self.assertTrue(isFunctionForWSClient(thisIsANewFunction), "new function is detected")

    def test_isFunctionForWSClient_ExcludesProtectedAndPrivateFunctions(self):
        def _thisIsAProtectedFunction(test):
            print(test)

        def __thisIsAPrivateFunction(test):
            print(test)

        self.assertFalse(isFunctionForWSClient(_thisIsAProtectedFunction), "protected function is excluded")
        self.assertFalse(isFunctionForWSClient(__thisIsAPrivateFunction), "private function is excluded")

    def test_isFunctionForWSClient_ExcludesAlreadyExistingFunctions(self):
        self.assertFalse(isFunctionForWSClient(HubsInspector.HUBs_DICT), "excludes existing functions")

    def test_getModulePath_ReturnsTestUtilsPyModulePath(self):
        self.assertIn("wshubsapi" + os.sep + "Test", getModulePath())

    def setUp_WSMessagesReceivedQueue(self, commEnvironment, MAX_WORKERS):
        queue = MessagesReceivedQueue(commEnvironment, MAX_WORKERS)
        return queue

    def test_WSMessagesReceivedQueue_Creates__MAX_WORKERS__WORKERS(self):
        queue = self.setUp_WSMessagesReceivedQueue(CommEnvironment(), 3)
        queue.executor.submit = flexmock()

        queue.startThreads()

    def setUp_WSMessagesReceivedQueue_infiniteOnMessageHandlerLoop(self, MAX_WORKERS, message):
        commEnvironment = flexmock(CommEnvironment())
        connectedClient = flexmock(ConnectedClient(commEnvironment, None))
        queue = self.setUp_WSMessagesReceivedQueue(commEnvironment, MAX_WORKERS)
        queue = flexmock(queue, get=lambda: [message, connectedClient])
        return queue, connectedClient, commEnvironment

    def test_WSMessagesReceivedQueue_infiniteOnMessageHandlerLoop_CallsClientOnMessage(self):
        queue, cc, commEnvironment = self.setUp_WSMessagesReceivedQueue_infiniteOnMessageHandlerLoop(1, "message")
        commEnvironment.should_receive("onMessage").with_args(cc, "message").once()
        queue.startThreads()
        time.sleep(0.02)
        queue.keepAlive = False

    def test_WSMessagesReceivedQueue_infiniteOnMessageHandlerLoop_CallsOnErrorIfRaisesException(self):
        queue, cc, commEnvironment = self.setUp_WSMessagesReceivedQueue_infiniteOnMessageHandlerLoop(1, "message")
        commEnvironment.should_receive("onMessage").and_raise(cc, Exception, "test").once()
        commEnvironment.should_receive("onError").with_args(cc, Exception).once()
        queue.startThreads()
        time.sleep(0.02)
        queue.keepAlive = False

    def test_WSMessagesReceivedQueue_infiniteOnMessageHandlerLoop_PrintExceptionIfConnectedClientIsNoConnectedClient(
            self):
        queue, cc, commEnvironment = self.setUp_WSMessagesReceivedQueue_infiniteOnMessageHandlerLoop(1, "message")
        queue.should_receive("get").and_return(["message", None]).once()
        commEnvironment.should_receive("onMessage").never()
        commEnvironment.should_receive("onError").never()

        queue.startThreads()
        time.sleep(0.02)
        queue.keepAlive = False
