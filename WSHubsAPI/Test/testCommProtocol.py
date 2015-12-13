# coding=utf-8
try:
    import thread
except ImportError:
    import _thread as thread
import unittest

from ConnectedClient import ConnectedClient
from WSHubsAPI.CommProtocol import CommProtocol
from WSHubsAPI.ConnectedClientsHolder import ConnectedClientsHolder
from WSHubsAPI.utils import WSMessagesReceivedQueue

try:
    from unittest.mock import MagicMock
except:
    from mock import MagicMock


class TestCommProtocol(unittest.TestCase):
    def setUp(self):
        self.commProtocol = CommProtocol(maxWorkers=0, unprovidedIdTemplate="unprovided_{}")

    def test_construct_initializeMandatoryAttributes(self):
        self.assertIsInstance(self.commProtocol.wsMessageReceivedQueue, WSMessagesReceivedQueue)
        self.assertIsInstance(self.commProtocol.lock, thread.LockType)
        self.assertIs(self.commProtocol.allConnectedClients, ConnectedClientsHolder.allConnectedClients)

    def test_ConstructConnectedClient_returnsConnectedClient(self):
        def w():
            pass

        def c():
            pass

        serialization = "serialization"
        connectedClient = self.commProtocol.constructConnectedClient(w, c, serialization)

        self.assertEqual(connectedClient.writeMessage, w)
        self.assertEqual(connectedClient.close, c)
        self.assertEqual(connectedClient.pickler, serialization)

    def test_getUnprovidedID_returnsFirstAvailableUnprovidedID(self):
        firstClient = ConnectedClient(None, self.commProtocol, lambda x: x, lambda z: z)
        secondClient = ConnectedClient(None, self.commProtocol, lambda x: x, lambda z: z)
        firstClient.onOpen()  # first UnprovidedID = unprovided_0
        secondClient.onOpen()  # first UnprovidedID = unprovided_1

        unprovidedId = self.commProtocol.getUnprovidedID()

        self.assertEqual(unprovidedId, "unprovided_2")

    def test_getUnprovidedID_returnAvailableUnprovidedIdsIfExist(self):
        self.commProtocol.availableUnprovidedIds.append("availableId_1")

        unprovidedId = self.commProtocol.getUnprovidedID()

        self.assertEqual(unprovidedId, "availableId_1")

    def test_getUnprovidedID_availableIdsAreRemovedWhenUsed(self):
        self.commProtocol.availableUnprovidedIds.append("availableId_1")
        unprovidedId1 = self.commProtocol.getUnprovidedID()
        unprovidedId2 = self.commProtocol.getUnprovidedID()

        self.assertEqual(unprovidedId2, "unprovided_0")