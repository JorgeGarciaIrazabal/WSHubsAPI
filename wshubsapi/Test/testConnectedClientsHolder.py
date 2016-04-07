# coding=utf-8
import unittest

from flexmock import flexmock
from wshubsapi.CommEnvironment import CommEnvironment

from wshubsapi.ConnectedClient import ConnectedClient
from wshubsapi.ConnectedClientsGroup import ConnectedClientsGroup
from wshubsapi.ConnectedClientsHolder import ConnectedClientsHolder


class TestConnectedClientsHolder(unittest.TestCase):
    def setUp(self):
        self.testHubName = "testHubName"
        self.connectedClientsHolder = ConnectedClientsHolder(self.testHubName)



        for i in range(10):
            connectedClient = flexmock(ConnectedClient(CommEnvironment(max_workers=0), None), ID=i)
            self.connectedClientsHolder.append_client(connectedClient)

    def test_getAllClients_returns10ConnectedClientsWithDifferentIDs(self):
        checkedIds = []

        allClients = self.connectedClientsHolder.get_all_clients()

        for i in range(10):
            self.assertNotIn(allClients[i].ID, checkedIds)
            checkedIds.append(allClients[i].ID)
            self.assertEqual(len(checkedIds), i + 1)

    def test_getOtherClients_returns9ConnectedClientsAndNotTheSender(self):
        sender = self.connectedClientsHolder.get_client(8)

        otherClients = self.connectedClientsHolder.get_other_clients(sender)

        self.assertEqual(len(otherClients), 9)
        for otherClient in otherClients:
            self.assertFalse(otherClient.ID == sender.ID)

    def test_getClients_returnsOnlyClientsWithEvenIDs(self):
        evenClients = filter(lambda x: x.ID % 2 == 0, self.connectedClientsHolder.get_all_clients())

        self.assertEqual(len(list(evenClients)), 5)
        for client in evenClients:
            self.assertTrue(client.ID % 2 == 0)

    def test_getClient_returnsClientWithID5(self):
        client3 = self.connectedClientsHolder.get_client(3)
        client5 = self.connectedClientsHolder.get_client(5)
        client7 = self.connectedClientsHolder.get_client(7)

        self.assertEqual(client3.ID, 3)
        self.assertEqual(client5.ID, 5)
        self.assertEqual(client7.ID, 7)


