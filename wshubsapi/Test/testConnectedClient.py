# coding=utf-8
import json
import unittest

from jsonpickle.pickler import Pickler

from wshubsapi.client_in_hub import ClientInHub
from wshubsapi.comm_environment import CommEnvironment
from wshubsapi.connected_client import ConnectedClient
from wshubsapi.connected_clients_holder import ConnectedClientsHolder
from wshubsapi.hub2 import Hub
from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.test.utils.HubsUtils import removeHubsSubclasses
from wshubsapi.test.utils.MessageCreator import MessageCreator
from flexmock import flexmock, flexmock_teardown


class TestConnectedClient(unittest.TestCase):
    def setUp(self):
        class TestHub(Hub):
            def __init__(self):
                super(TestHub, self).__init__()
                self.testFunctionReplayArg = lambda x: x
                self.testFunctionReplayNone = lambda: None

            def testFunctionError(self):
                raise Exception("Error")

        class ClientMock:
            def __init__(self):
                self.writeMessage = flexmock()
                self.close = flexmock()
                pass

        flexmock(CommEnvironment, __check_futures=lambda *args: None)

        HubsInspector.inspect_implemented_hubs(force_reconstruction=True)
        self.testHubClass = TestHub
        self.testHubInstance = HubsInspector.get_hub_instance(self.testHubClass)

        self.jsonPickler = Pickler(max_depth=3, max_iter=30, make_refs=False)
        self.commEnvironment = CommEnvironment(max_workers=0, unprovided_id_template="unprovidedTest__{}")
        self.clientMock = ClientMock()
        self.connectedClient = ConnectedClient(self.commEnvironment, self.clientMock.writeMessage)
        self.connectedClientsHolder = ConnectedClientsHolder(self.testHubClass.__HubName__)

    def tearDown(self):
        flexmock_teardown()
        self.connectedClientsHolder.all_connected_clients.clear()
        del self.testHubClass
        del self.testHubInstance
        removeHubsSubclasses()

    def test_onOpen_appendsClientInConnectedClientsHolderWithDefinedID(self):
        ID = 3

        self.commEnvironment.on_opened(self.connectedClient, ID)

        self.assertIsInstance(self.connectedClientsHolder.get_client(ID), ClientInHub)

    def test_onOpen_appendsUndefinedIdIfNoIDIsDefine(self):
        self.commEnvironment.on_opened(self.connectedClient)

        self.assertIsInstance(self.connectedClientsHolder.get_client("unprovidedTest__0"), ClientInHub)

    def test_onOpen_appendsUndefinedIdIfOpenAlreadyExistingClientId(self):
        self.commEnvironment.on_opened(self.connectedClient, 3)
        secondId = self.commEnvironment.on_opened(self.connectedClient, 3)

        self.assertEqual(secondId, "unprovidedTest__0")
        self.assertIsInstance(self.connectedClientsHolder.get_client(3), ClientInHub)
        self.assertIsInstance(self.connectedClientsHolder.get_client(secondId), ClientInHub)

    def __setUp_onMessage(self, functionStr, args, replay, success=True):
        message = MessageCreator.createOnMessageMessage(hub=self.testHubClass.__HubName__,
                                                        function=functionStr,
                                                        args=args)
        replayMessage = MessageCreator.createReplayMessage(hub=self.testHubClass.__HubName__,
                                                           function=functionStr,
                                                           replay=replay,
                                                           success=success)
        messageStr = json.dumps(message)
        self.commEnvironment = flexmock(self.commEnvironment)

        return messageStr, replayMessage

    def test_onMessage_callsReplayIfSuccess(self):
        messageStr, replayMessage = self.__setUp_onMessage("testFunctionReplayArg", [1], 1)
        self.commEnvironment.should_receive("replay").with_args(self.connectedClient, replayMessage, messageStr).once()

        self.commEnvironment.on_message(self.connectedClient, messageStr)

    def test_onMessage_callsOnErrorIfError(self):
        messageStr, replayMessage = self.__setUp_onMessage("testFunctionError", [], dict, success=False)
        self.commEnvironment.should_receive("replay").with_args(self.connectedClient, dict, messageStr).once()

        self.commEnvironment.on_message(self.connectedClient, messageStr)

    def test_onMessage_notCallsReplayIfFunctionReturnNone(self):
        messageStr, replayMessage = self.__setUp_onMessage("testFunctionReplayNone", [], None)
        self.commEnvironment.should_receive("replay").never()

        self.commEnvironment.on_message(self.connectedClient, messageStr)

    def test_onMessage_onErrorIsCalledIfMessageCanNotBeParsed(self):
        messageStr, replayMessage = self.__setUp_onMessage("testFunctionReplayNone", [], None)
        self.commEnvironment.should_receive("replay").never()
        self.commEnvironment.should_receive("on_error").once()

        self.commEnvironment.on_message(self.connectedClient, messageStr + "breaking message")

    def test_onAsyncMessage_putsTheMessageAndTheConnectionInTheQueue(self):
        message = MessageCreator.createOnMessageMessage()
        self.commEnvironment.wsMessageReceivedQueue = flexmock(self.commEnvironment.message_received_queue)
        self.commEnvironment.wsMessageReceivedQueue.should_receive("put").with_args((message, self.connectedClient)).once()

        self.commEnvironment.on_async_message(self.connectedClient, message)

    def test_onClose_removeExistingConnectedClient(self):
        ID = 3
        self.commEnvironment.on_opened(self.connectedClient, ID)

        self.commEnvironment.on_closed(self.connectedClient)

        self.assertRaises(KeyError, self.connectedClientsHolder.get_client, ID)
        self.assertEqual(len(self.connectedClientsHolder.all_connected_clients), 0)

    def test_replay_writeMessageWithAString(self):
        replayMessage = MessageCreator.createReplayMessage()
        self.connectedClient = flexmock(self.connectedClient)
        self.connectedClient.should_receive("api_write_message").with_args(str).once()

        self.commEnvironment.replay(self.connectedClient, replayMessage, "test")
