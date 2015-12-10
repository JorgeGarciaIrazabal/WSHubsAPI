# coding=utf-8
import unittest

from jsonpickle.pickler import Pickler

from CommProtocol import CommProtocol

try:
    from unittest.mock import MagicMock
except:
    from mock import MagicMock


class TestConnectedClientsHolder(unittest.TestCase):
    def setUp(self):
        self.jsonPickler = Pickler(max_depth=3, max_iter=30, make_refs=False)
        self.commProtocol = CommProtocol(unprovidedIdTemplate="unprovidedTest__%d")

        class ClientMock:
            def __init__(self):
                self.writeMessage = MagicMock(return_value="messageReceived")
                self.close = MagicMock(return_value="close")
                pass

        self.clientMock = ClientMock()
        self.commProtocol = CommProtocol()
        self.connectedClient = self.commProtocol.constructConnectedClient(self.clientMock.writeMessage,
                                                                          self.clientMock.close)

    def test_getAllClients_returns10ConnectedClientsWithDifferentIDs(self):
        checkedIds = []

        allClients = self.connectedClientsHolder.getAllClients()

        for i in range(10):
            self.assertNotIn(allClients[i].ID, checkedIds)
            checkedIds.append(allClients[i].ID)
            self.assertEqual(len(checkedIds), i + 1)

    def test_getOtherClients_returns9ConnectedClientsAndNotTheSender(self):
        sender = filter(lambda x: x.ID == 8, self.connectedClientsHolder.getAllClients())[0]

        otherClients = self.connectedClientsHolder.getOtherClients(sender)

        self.assertEqual(len(otherClients), 9)
        for otherClient in otherClients:
            self.assertFalse(otherClient.ID == sender.ID)

    def test_getClients_returnsOnlyClientsWithEvenIDs(self):
        evenClients = filter(lambda x: x.ID % 2 == 0, self.connectedClientsHolder.getAllClients())

        self.assertEqual(len(evenClients), 5)
        for client in evenClients:
            self.assertTrue(client.ID % 2 == 0)

    def test_getClient_returnsClientWithID5(self):
        client3 = self.connectedClientsHolder.getClient(3)
        client5 = self.connectedClientsHolder.getClient(5)
        client7 = self.connectedClientsHolder.getClient(7)

        self.assertEqual(client3[0].ID, 3)
        self.assertEqual(client5[0].ID, 5)
        self.assertEqual(client7[0].ID, 7)
