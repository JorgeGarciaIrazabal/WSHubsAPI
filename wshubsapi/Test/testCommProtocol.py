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
        self.commEnvironment = CommEnvironment(max_workers=0, unprovided_id_template="unprovided_{}")

    def test_construct_initializeMandatoryAttributes(self):
        self.assertIsInstance(self.commEnvironment.message_received_queue, MessagesReceivedQueue)
        self.assertIsInstance(self.commEnvironment.lock, thread.LockType)
        self.assertIs(self.commEnvironment.all_connected_clients, ConnectedClientsHolder.allConnectedClientsDict)

    def test_getUnprovidedID_returnsFirstAvailableUnprovidedID(self):
        firstClient = ConnectedClient(self.commEnvironment, lambda x: x)
        secondClient = ConnectedClient(self.commEnvironment, lambda x: x)
        self.commEnvironment.on_opened(firstClient)  # first UnprovidedID = unprovided_0
        self.commEnvironment.on_opened(secondClient)  # first UnprovidedID = unprovided_1

        unprovidedId = self.commEnvironment.get_unprovided_id()

        self.assertEqual(unprovidedId, "unprovided_2")

    def test_getUnprovidedID_returnAvailableUnprovidedIdsIfExist(self):
        self.commEnvironment.available_unprovided_ids.append("availableId_1")

        unprovidedId = self.commEnvironment.get_unprovided_id()

        self.assertEqual(unprovidedId, "availableId_1")

    def test_getUnprovidedID_availableIdsAreRemovedWhenUsed(self):
        self.commEnvironment.available_unprovided_ids.append("availableId_1")
        unprovidedId1 = self.commEnvironment.get_unprovided_id()
        unprovidedId2 = self.commEnvironment.get_unprovided_id()

        self.assertEqual(unprovidedId2, "unprovided_0")
