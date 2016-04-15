# coding=utf-8
import unittest

from wshubsapi.client_in_hub import ClientInHub
from wshubsapi.connected_client import ConnectedClient
from wshubsapi.function_message import FunctionMessage
from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.hub2 import Hub
from wshubsapi.test.utils.HubsUtils import removeHubsSubclasses


class TestFunctionMessage(unittest.TestCase):
    def setUp(self):
        class TestHub(Hub):
            def testMethod(self, x, _sender, y=1):
                return x, _sender, y

            def testException(self):
                raise Exception("MyException")

            def testNoSender(self, x):
                return x

            def testReplayUnsuccessful(self, x):
                return self._construct_unsuccessful_replay(x)

        self.testHubClass = TestHub
        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)
        self.testHubInstance = HubsInspector.get_hub_instance(self.testHubClass)

    def tearDown(self):
        del self.testHubClass
        del self.testHubInstance
        removeHubsSubclasses()

    def __constructMessageStr(self, hub="TestHub", function="testMethod", ID=1, args=list()):
        message = {
            "hub": hub,
            "function": function,
            "args": args,
            "ID": ID
        }
        return message

    def test_FunctionMessageConstruction_InitializeNecessaryAttributes(self):
        fn = FunctionMessage(self.__constructMessageStr(), "connectedClient")

        self.assertEqual(fn.hub_instance, self.testHubInstance)
        self.assertEqual(fn.hub_name, self.testHubClass.__HubName__)
        self.assertEqual(fn.args, [])
        self.assertEqual(fn.method, self.testHubInstance.testMethod)
        self.assertEqual(fn.connected_client, "connectedClient")

    def test_FunctionMessageConstruction_WithUnrealMethodNameRaisesAnError(self):
        message = self.__constructMessageStr(function="notExists")
        self.assertRaises(AttributeError, FunctionMessage, message, "connectedClient")

    def test_CallFunction_ReturnsAnExpectedReplayMessageIfSuccess(self):
        fn = FunctionMessage(self.__constructMessageStr(args=["x"], ID=15, function="testNoSender"), "_sender")

        functionResult = fn.call_function()

        self.assertEqual(functionResult["replay"], "x")
        self.assertEqual(functionResult["success"], True)
        self.assertEqual(functionResult["hub"], self.testHubClass.__HubName__)
        self.assertEqual(functionResult["function"], "testNoSender")
        self.assertEqual(functionResult["ID"], 15)

    def test_CallFunction_ReturnsAnExpectedReplayMessageIfNoSuccess(self):
        fn = FunctionMessage(self.__constructMessageStr(ID=15, function="testException"), "_sender")

        functionResult = fn.call_function()

        self.assertEqual(functionResult["success"], False)
        self.assertEqual(functionResult["hub"], self.testHubClass.__HubName__)
        self.assertEqual(functionResult["function"], "testException")
        self.assertEqual(functionResult["ID"], 15)

    def test_CallFunction_IncludesSender(self):
        cc = ConnectedClient(None, None)
        fn = FunctionMessage(self.__constructMessageStr(args=["x"]), cc)

        functionResult = fn.call_function()

        self.assertEqual(functionResult["replay"][0], "x")
        self.assertIsInstance(functionResult["replay"][1], ClientInHub)
        self.assertEqual(functionResult["replay"][1].api_get_real_connected_client(), cc)
        self.assertEqual(functionResult["replay"][2], 1)
        self.assertEqual(functionResult["success"], True)

    def test_CallFunction_DoesNotIncludesSenderIfNotRequested(self):
        fn = FunctionMessage(self.__constructMessageStr(args=["x"], function="testNoSender"), "_sender")

        functionResult = fn.call_function()

        self.assertEqual(functionResult["replay"], "x")
        self.assertEqual(functionResult["success"], True)

    def test_CallFunction_SuccessFalseIfMethodRaisesException(self):
        fn = FunctionMessage(self.__constructMessageStr(function="testException"), "_sender")

        functionResult = fn.call_function()

        self.assertEqual(functionResult["success"], False)
        self.assertEqual(functionResult["replay"]["error"], "MyException")

    def test_CallFunction_ReplaysSuccessFalseIfReturnsUnsuccessfulReplayObject(self):
        fn = FunctionMessage(self.__constructMessageStr(function="testReplayUnsuccessful", args=["x"]), "_sender")

        functionResult = fn.call_function()

        self.assertEqual(functionResult["success"], False)
        self.assertEqual(functionResult["replay"], "x")
