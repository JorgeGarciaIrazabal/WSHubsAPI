# coding=utf-8
import json
import unittest

from jsonpickle.pickler import Pickler

from wshubsapi.client_in_hub import ClientInHub
from wshubsapi.comm_environment import CommEnvironment
from wshubsapi.connected_client import ConnectedClient
from wshubsapi.connected_clients_holder import ConnectedClientsHolder
from wshubsapi.hub import Hub
from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.test.utils.hubs_utils import remove_hubs_subclasses
from wshubsapi.test.utils.message_creator import MessageCreator
from flexmock import flexmock, flexmock_teardown


class TestConnectedClient(unittest.TestCase):
    def setUp(self):
        class TestHub(Hub):
            def __init__(self):
                super(TestHub, self).__init__()
                self.testFunctionReplayArg = lambda x: x
                self.testFunctionReplayNone = lambda: None

            def test_function_error(self):
                raise Exception("Error")

        class ClientMock:
            def __init__(self):
                self.writeMessage = flexmock()
                self.close = flexmock()
                pass

        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)
        self.testHubClass = TestHub
        self.testHubInstance = HubsInspector.get_hub_instance(self.testHubClass)

        self.jsonPickler = Pickler(max_depth=3, max_iter=30, make_refs=False)
        self.commEnvironment = CommEnvironment(unprovided_id_template="unprovidedTest__{}")
        self.clientMock = ClientMock()
        self.connectedClient = ConnectedClient(self.commEnvironment, self.clientMock.writeMessage)
        self.connectedClientsHolder = ConnectedClientsHolder(self.testHubInstance)
        self.connectedClientsHolder.all_connected_clients.clear()

    def tearDown(self):
        flexmock_teardown()
        self.connectedClientsHolder.all_connected_clients.clear()
        del self.testHubClass
        del self.testHubInstance
        del self.connectedClientsHolder.hub_instance
        remove_hubs_subclasses()

    def test_onOpen_appendsClientInConnectedClientsHolderWithDefinedID(self):
        id_ = 3

        self.commEnvironment.on_opened(self.connectedClient, id_)

        self.assertIsInstance(self.connectedClientsHolder.get_client(id_), ClientInHub)

    def test_onOpen_appendsUndefinedIdIfNoIDIsDefine(self):
        self.commEnvironment.on_opened(self.connectedClient)

        self.assertIsInstance(self.connectedClientsHolder.get_client("unprovidedTest__0"), ClientInHub)

    def test_onOpen_appendsUndefinedIdIfOpenAlreadyExistingClientId(self):
        self.commEnvironment.on_opened(self.connectedClient, 3)
        second_id = self.commEnvironment.on_opened(self.connectedClient, 3)

        self.assertEqual(second_id, "unprovidedTest__0")
        self.assertIsInstance(self.connectedClientsHolder.get_client(3), ClientInHub)
        self.assertIsInstance(self.connectedClientsHolder.get_client(second_id), ClientInHub)

    def __set_up_on_message(self, function_str, args, reply, success=True):
        message = MessageCreator.create_on_message_message(hub=self.testHubClass.__HubName__,
                                                           function=function_str,
                                                           args=args)
        replay_message = MessageCreator.create_replay_message(hub=self.testHubClass.__HubName__,
                                                              function=function_str,
                                                              reply=reply,
                                                              success=success)
        message_str = json.dumps(message)
        self.commEnvironment = flexmock(self.commEnvironment)

        return message_str, replay_message

    def test_onMessage_callsReplayIfSuccess(self):
        message_str, replay_message = self.__set_up_on_message("testFunctionReplayArg", [1], 1)
        self.commEnvironment.should_receive("reply").with_args(self.connectedClient, replay_message, message_str).once()

        self.commEnvironment.on_message(self.connectedClient, message_str)

    def test_onMessage_callsOnErrorIfError(self):
        message_str, replay_message = self.__set_up_on_message("testFunctionError", [], dict, success=False)
        self.commEnvironment.should_receive("__on_replay").with_args(self.connectedClient, message_str, dict).once()

        self.commEnvironment.on_message(self.connectedClient, message_str)

    def test_onMessage_notCallsReplayIfFunctionReturnNone(self):
        message_str, replay_message = self.__set_up_on_message("testFunctionReplayNone", [], None)
        self.commEnvironment.should_receive("reply").never()

        self.commEnvironment.on_message(self.connectedClient, message_str)

    def test_onMessage_onErrorIsCalledIfMessageCanNotBeParsed(self):
        message_str, replay_message = self.__set_up_on_message("testFunctionReplayNone", [], None)
        self.commEnvironment.should_receive("reply").never()
        self.commEnvironment.should_receive("on_error").once()

        self.commEnvironment.on_message(self.connectedClient, message_str + "breaking message")

    def test_onClose_removeExistingConnectedClient(self):
        id_ = 3
        self.commEnvironment.on_opened(self.connectedClient, id_)

        self.commEnvironment.on_closed(self.connectedClient)

        self.assertRaises(KeyError, self.connectedClientsHolder.get_client, id_)
        self.assertEqual(len(self.connectedClientsHolder.all_connected_clients), 0)

    def test_replay_writeMessageWithAString(self):
        replay_message = MessageCreator.create_replay_message()
        self.connectedClient = flexmock(self.connectedClient)
        self.connectedClient.should_receive("api_write_message").with_args(str).once()

        self.commEnvironment.reply(self.connectedClient, replay_message, "test")
