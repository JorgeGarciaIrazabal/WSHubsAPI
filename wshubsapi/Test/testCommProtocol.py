# coding=utf-8
try:
    import thread
except ImportError:
    import _thread as thread
import unittest

from wshubsapi.ConnectedClient import ConnectedClient
from wshubsapi.CommEnvironment import CommEnvironment
from wshubsapi.ConnectedClientsHolder import ConnectedClientsHolder
from wshubsapi.MessagesReceivedQueue import MessagesReceivedQueue


class TestCommProtocol(unittest.TestCase):
    def setUp(self):
        self.commEnvironment = CommEnvironment(maxWorkers=0, unprovidedIdTemplate="unprovided_{}")

    def test_construct_initializeMandatoryAttributes(self):
        self.assertIsInstance(self.commEnvironment.wsMessageReceivedQueue, MessagesReceivedQueue)
        self.assertIsInstance(self.commEnvironment.lock, thread.LockType)
        self.assertIs(self.commEnvironment.allConnectedClients, ConnectedClientsHolder.allConnectedClientsDict)

    def test_getUnprovidedID_returnsFirstAvailableUnprovidedID(self):
        firstClient = ConnectedClient(self.commEnvironment, lambda x: x)
        secondClient = ConnectedClient(self.commEnvironment, lambda x: x)
        self.commEnvironment.onOpen(firstClient)  # first UnprovidedID = unprovided_0
        self.commEnvironment.onOpen(secondClient)  # first UnprovidedID = unprovided_1

        unprovidedId = self.commEnvironment.getUnprovidedID()

        self.assertEqual(unprovidedId, "unprovided_2")

    def test_getUnprovidedID_returnAvailableUnprovidedIdsIfExist(self):
        self.commEnvironment.availableUnprovidedIds.append("availableId_1")

        unprovidedId = self.commEnvironment.getUnprovidedID()

        self.assertEqual(unprovidedId, "availableId_1")

    def test_getUnprovidedID_availableIdsAreRemovedWhenUsed(self):
        self.commEnvironment.availableUnprovidedIds.append("availableId_1")
        unprovidedId1 = self.commEnvironment.getUnprovidedID()
        unprovidedId2 = self.commEnvironment.getUnprovidedID()

        self.assertEqual(unprovidedId2, "unprovided_0")
