# coding=utf-8
import json
import unittest

from jsonpickle.pickler import Pickler

from wshubsapi.CommEnvironment import CommEnvironment
from wshubsapi.ConnectedClientsHolder import ConnectedClientsHolder
from wshubsapi.Hub import Hub
from wshubsapi.HubsInspector import HubsInspector
from wshubsapi.Test.utils.HubsUtils import removeHubsSubclasses
from wshubsapi.Test.utils.MessageCreator import MessageCreator
from flexmock import flexmock


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

        HubsInspector.inspectImplementedHubs(forceReconstruction=True)
        self.testHubClass = TestHub
        self.testHubInstance = HubsInspector.getHubInstance(self.testHubClass)

        self.jsonPickler = Pickler(max_depth=3, max_iter=30, make_refs=False)
        self.commEnvironment = CommEnvironment(maxWorkers=0, unprovidedIdTemplate="unprovidedTest__{}")
        self.clientMock = ClientMock()
        self.connectedClient = self.commEnvironment.constructConnectedClient(self.clientMock.writeMessage,
                                                                             self.jsonPickler)
        self.connectedClientsHolder = ConnectedClientsHolder(self.testHubClass.__HubName__)

    def tearDown(self):
        self.connectedClientsHolder.allConnectedClientsDict.clear()
        del self.testHubClass
        del self.testHubInstance
        removeHubsSubclasses()

    def test_onOpen_appendsClientInConnectedClientsHolderWithDefinedID(self):
        ID = 3

        self.connectedClient.onOpen(ID)

        self.assertTrue(len(self.connectedClientsHolder.getClient(ID)), 1)

    def test_onOpen_appendsUndefinedIdIfNoIDIsDefine(self):
        self.connectedClient.onOpen()

        self.assertTrue(len(self.connectedClientsHolder.getClient("unprovidedTest__0")), 1)

    def test_onOpen_appendsUndefinedIdIfOpenAlreadyExistingClientId(self):
        self.connectedClient.onOpen(3)
        secondId = self.connectedClient.onOpen(3)

        self.assertEqual(secondId, "unprovidedTest__0")
        self.assertTrue(len(self.connectedClientsHolder.getClient(3)), 1)
        self.assertTrue(len(self.connectedClientsHolder.getClient(secondId)), 1)

    def __setUp_onMessage(self, functionStr, args, replay, success=True):
        message = MessageCreator.createOnMessageMessage(hub=self.testHubClass.__HubName__,
                                                        function=functionStr,
                                                        args=args)
        replayMessage = MessageCreator.createReplayMessage(hub=self.testHubClass.__HubName__,
                                                           function=functionStr,
                                                           replay=replay,
                                                           success=success)
        messageStr = json.dumps(message)
        self.connectedClient = flexmock(self.connectedClient)

        return messageStr, replayMessage

    def test_onMessage_callsReplayIfSuccess(self):
        messageStr, replayMessage = self.__setUp_onMessage("testFunctionReplayArg", [1], 1)
        self.connectedClient.should_receive("replay").with_args(replayMessage, messageStr).once()

        self.connectedClient.onMessage(messageStr)

    def test_onMessage_callsOnErrorIfError(self):
        messageStr, replayMessage = self.__setUp_onMessage("testFunctionError", [], "Error", success=False)
        self.connectedClient.should_receive("replay").with_args(replayMessage, messageStr).once()

        self.connectedClient.onMessage(messageStr)

    def test_onMessage_notCallsReplayIfFunctionReturnNone(self):
        messageStr, replayMessage = self.__setUp_onMessage("testFunctionReplayNone", [], None)
        self.connectedClient.should_receive("replay").never()

        self.connectedClient.onMessage(messageStr)

    def test_onMessage_onErrorIsCalledIfMessageCanNotBeParsed(self):
        messageStr, replayMessage = self.__setUp_onMessage("testFunctionReplayNone", [], None)
        self.connectedClient.should_receive("replay").never()
        self.connectedClient.should_receive("onError").once()

        self.connectedClient.onMessage(messageStr + "breaking message")

    def test_onAsyncMessage_putsTheMessageAndTheConnectionInTheQueue(self):
        message = MessageCreator.createOnMessageMessage()
        self.commEnvironment.wsMessageReceivedQueue = flexmock(self.commEnvironment.wsMessageReceivedQueue)
        self.commEnvironment.wsMessageReceivedQueue.should_receive("put").with_args((message, self.connectedClient)).once()

        self.connectedClient.onAsyncMessage(message)

    def test_onClose_removeExistingConnectedClient(self):
        ID = 3
        self.connectedClient.onOpen(ID)

        self.connectedClient.onClosed()

        self.assertRaises(KeyError, self.connectedClientsHolder.getClient, ID)
        self.assertEqual(len(self.connectedClientsHolder.allConnectedClientsDict), 0)

    def test_replay_writeMessageWithAString(self):
        replayMessage = MessageCreator.createReplayMessage()
        self.connectedClient = flexmock(self.connectedClient)
        self.connectedClient.should_receive("writeMessage").with_args(str).once()

        self.connectedClient.replay(replayMessage, "test")
