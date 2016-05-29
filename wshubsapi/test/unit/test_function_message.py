# coding=utf-8
import unittest

from flexmock import flexmock, flexmock_teardown

from wshubsapi.client_in_hub import ClientInHub
from wshubsapi.connected_client import ConnectedClient
from wshubsapi.function_message import FunctionMessage
from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.hub import Hub
from wshubsapi.test.utils.hubs_utils import remove_hubs_subclasses


class TestFunctionMessage(unittest.TestCase):
    def setUp(self):
        class TestHub(Hub):
            def test_method(self, x, _sender, y=1):
                return x, _sender, y

            def test_exception(self):
                raise Exception("MyException")

            def test_no_sender(self, x):
                return x

            def test_replay_unsuccessful(self, x):
                return self._construct_unsuccessful_replay(x)

        self.env_mock = flexmock(debug_mode=True)
        self.testHubClass = TestHub
        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)
        self.testHubInstance = HubsInspector.get_hub_instance(self.testHubClass)

    def tearDown(self):
        del self.testHubClass
        del self.testHubInstance
        remove_hubs_subclasses()
        flexmock_teardown()

    def __constructMessageStr(self, hub="TestHub", function="test_method", ID=1, args=list()):
        message = {
            "hub": hub,
            "function": function,
            "args": args,
            "ID": ID
        }
        return message

    def test_FunctionMessageConstruction_InitializeNecessaryAttributes(self):
        fn = FunctionMessage(self.__constructMessageStr(), "connectedClient", self.env_mock)

        self.assertEqual(fn.hub_instance, self.testHubInstance)
        self.assertEqual(fn.hub_name, self.testHubClass.__HubName__)
        self.assertEqual(fn.args, [])
        self.assertEqual(fn.method, self.testHubInstance.test_method)
        self.assertEqual(fn.connected_client, "connectedClient")

    def test_FunctionMessageConstruction_WithUnrealMethodNameRaisesAnError(self):
        message = self.__constructMessageStr(function="notExists")
        self.assertRaises(AttributeError, FunctionMessage, message, "connectedClient", self.env_mock)

    def test_CallFunction_ReturnsAnExpectedReplayMessageIfSuccess(self):
        fn = FunctionMessage(self.__constructMessageStr(args=["x"], ID=15, function="test_no_sender"), "_sender",
                             self.env_mock)

        function_result = fn.call_function()

        self.assertEqual(function_result["reply"], "x")
        self.assertEqual(function_result["success"], True)
        self.assertEqual(function_result["hub"], self.testHubClass.__HubName__)
        self.assertEqual(function_result["function"], "test_no_sender")
        self.assertEqual(function_result["ID"], 15)

    def test_CallFunction_ReturnsAnExpectedReplayMessageIfNoSuccess(self):
        fn = FunctionMessage(self.__constructMessageStr(ID=15, function="test_exception"), "_sender", self.env_mock)

        function_result = fn.call_function()

        self.assertEqual(function_result["success"], False)
        self.assertEqual(function_result["hub"], self.testHubClass.__HubName__)
        self.assertEqual(function_result["function"], "test_exception")
        self.assertEqual(function_result["ID"], 15)

    def test_CallFunction_IncludesSender(self):
        cc = ConnectedClient(None, None)
        fn = FunctionMessage(self.__constructMessageStr(args=["x"]), cc, self.env_mock)

        function_result = fn.call_function()

        self.assertEqual(function_result["reply"][0], "x")
        self.assertIsInstance(function_result["reply"][1], ClientInHub)
        self.assertEqual(function_result["reply"][1].api_get_real_connected_client(), cc)
        self.assertEqual(function_result["reply"][2], 1)
        self.assertEqual(function_result["success"], True)

    def test_CallFunction_DoesNotIncludesSenderIfNotRequested(self):
        fn = FunctionMessage(self.__constructMessageStr(args=["x"], function="test_no_sender"), "_sender", self.env_mock)

        function_result = fn.call_function()

        self.assertEqual(function_result["reply"], "x")
        self.assertEqual(function_result["success"], True)

    def test_CallFunction_SuccessFalseIfMethodRaisesException(self):
        fn = FunctionMessage(self.__constructMessageStr(function="test_exception"), "_sender", self.env_mock)

        function_result = fn.call_function()

        self.assertEqual(function_result["success"], False)
        self.assertEqual(function_result["reply"]["error"], "MyException")

    def test_CallFunction_ReplaysSuccessFalseIfReturnsUnsuccessfulReplayObject(self):
        fn = FunctionMessage(self.__constructMessageStr(function="test_replay_unsuccessful", args=["x"]), "_sender",
                             self.env_mock)

        function_result = fn.call_function()

        self.assertEqual(function_result["success"], False)
        self.assertEqual(function_result["reply"], "x")
