# coding=utf-8
import unittest
import pprint

from flexmock import flexmock, flexmock_teardown

from wshubsapi.comm_environment import CommEnvironment
from wshubsapi.connected_client import ConnectedClient
from wshubsapi.connected_clients_holder import ConnectedClientsHolder


class TestConnectedClientsHolder(unittest.TestCase):
    def setUp(self):
        self.test_hub_name = "testHubName"
        self.clients_holder = ConnectedClientsHolder(self.test_hub_name)
        ConnectedClientsHolder.all_connected_clients = dict()
        flexmock(CommEnvironment, __check_futures=lambda *args: None)

        for i in range(10):
            connected_client = flexmock(ConnectedClient(CommEnvironment(max_workers=0), None))
            connected_client.ID = i
            self.clients_holder.append_client(connected_client)

    def tearDown(self):
        flexmock_teardown()

    def test_get_all_clients__returns_10_connected_clients_with_different_ids(self):
        checked_ids = []

        all_clients = self.clients_holder.get_all_clients()

        for i in range(10):
            self.assertNotIn(all_clients[i].ID, checked_ids)
            checked_ids.append(all_clients[i].ID)
            self.assertEqual(len(checked_ids), i + 1)

    def test_get_other_clients__returns_9_connected_clients_and_not_the_sender(self):
        sender = self.clients_holder.get_client(8)

        other_clients = self.clients_holder.get_other_clients(sender)

        self.assertEqual(len(other_clients), 9)
        for otherClient in other_clients:
            self.assertFalse(otherClient.ID == sender.ID)

    def test_get_clients__returns_only_clients_with_even_ids(self):
        even_clients = filter(lambda x: x.ID % 2 == 0, self.clients_holder.get_all_clients())

        self.assertEqual(len(list(even_clients)), 5)
        for client in even_clients:
            self.assertTrue(client.ID % 2 == 0)

    def test_get_client__returns_client_with_ids(self):
        client3 = self.clients_holder.get_client(3)
        client5 = self.clients_holder.get_client(5)
        client7 = self.clients_holder.get_client(7)

        self.assertEqual(client3.ID, 3)
        self.assertEqual(client5.ID, 5)
        self.assertEqual(client7.ID, 7)

    def test_get__returns_only_clients_with_odd_ids_passing_filter_function(self):
        def only_odds(x):
            return x.ID % 2 != 0

        odd_clients = self.clients_holder.get(only_odds)

        self.assertEqual(len(list(odd_clients)), 5)
        for client in odd_clients:
            self.assertTrue(client.ID % 2 != 0)

    def test_get__returns_clients_list_with_ids_as_param(self):
        clients = self.clients_holder.get([3, 5, 6])

        self.assertEqual(clients[0].ID, 3)
        self.assertEqual(clients[1].ID, 5)
        self.assertEqual(clients[2].ID, 6)

    def test_get__returns_client_with_id_as_param(self):
        client3 = self.clients_holder.get(3)
        client5 = self.clients_holder.get(5)
        client7 = self.clients_holder.get(7)

        self.assertEqual(client3.ID, 3)
        self.assertEqual(client5.ID, 5)
        self.assertEqual(client7.ID, 7)
