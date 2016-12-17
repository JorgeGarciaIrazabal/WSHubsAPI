# coding=utf-8
import unittest
from flexmock import flexmock, flexmock_teardown

from wshubsapi.client_in_hub import ClientInHub
from wshubsapi.comm_environment import CommEnvironment
from wshubsapi.connected_client import ConnectedClient
from wshubsapi.connected_clients_holder import ConnectedClientsHolder
from wshubsapi.hub import Hub
from wshubsapi.serializer import Serializer
from wshubsapi.test.utils.hubs_utils import remove_hubs_subclasses


class TestConnectedClientsHolder(unittest.TestCase):
    def setUp(self):

        class MyHub(Hub):
            __HubName__ = "testHubName"

        self.test_hub_name = "testHubName"
        self.clients_holder = MyHub()._clients_holder
        ConnectedClientsHolder.all_connected_clients = dict()

        for i in range(10):
            connected_client = flexmock(ConnectedClient(CommEnvironment(), None))
            connected_client.ID = i
            self.clients_holder.append_client(connected_client)

    def tearDown(self):
        flexmock_teardown()
        del self.clients_holder
        remove_hubs_subclasses()

    def __check_clients_are_well_constructed(self, clients_group):
        """
        :type clients_group: wshubsapi.connected_clients_group.ConnectedClientsGroup
        """
        self.assertEqual(clients_group.hub_name, self.test_hub_name)
        for c in clients_group:
            self.assertIsInstance(c, ClientInHub)

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
        self.__check_clients_are_well_constructed(other_clients)

    def test_get_clients__returns_only_clients_with_even_ids(self):
        even_clients = self.clients_holder.get_clients(lambda x: x.ID % 2 == 0)

        self.assertEqual(len(list(even_clients)), 5)
        for client in even_clients:
            self.assertTrue(client.ID % 2 == 0)
        self.__check_clients_are_well_constructed(even_clients)

    def test_get_client__returns_client_with_ids(self):
        client3 = self.clients_holder.get_client(3)
        client5 = self.clients_holder.get_client(5)
        client7 = self.clients_holder.get_client(7)

        self.assertEqual(client3.ID, 3)
        self.assertEqual(client5.ID, 5)
        self.assertEqual(client7.ID, 7)

    def test_get_clients__is_well_constructed(self):
        client = self.clients_holder.get_client(1)
        self.message_checked = False
        serializer = Serializer()

        def message_to_write(msg):
            json_msg = serializer.unserialize(msg)
            self.assertEqual(json_msg["function"], "test_call_function")
            self.assertEqual(json_msg["hub"], self.test_hub_name)
            self.message_checked = True

        client.api_get_real_connected_client().api_write_message = message_to_write
        client.test_call_function()
        self.assertTrue(self.message_checked)

    def test_get_subscribed_clients__returns_only_subscribed_clients(self):
        self.clients_holder.hub_instance.subscribe_to_hub(self.clients_holder.get_client(3))
        self.clients_holder.hub_instance.subscribe_to_hub(self.clients_holder.get_client(1))
        subscribed_clients = self.clients_holder.get_subscribed_clients()

        self.assertEqual(len(list(subscribed_clients)), 2)
        self.assertTrue(subscribed_clients[0].ID == 3)
        self.assertTrue(subscribed_clients[1].ID == 1)
        self.__check_clients_are_well_constructed(subscribed_clients)

    def test_get__returns_only_clients_with_odd_ids_passing_filter_function(self):
        def only_odds(x):
            return x.ID % 2 != 0

        odd_clients = self.clients_holder.get(only_odds)

        self.assertEqual(len(list(odd_clients)), 5)
        for client in odd_clients:
            self.assertTrue(client.ID % 2 != 0)
        self.__check_clients_are_well_constructed(odd_clients)

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

    def test_append_client_adds_a_client_if_not_exists(self):
        old_clients_length = len(self.clients_holder.get_all_clients())
        removed_client = self.clients_holder.pop_client(self.clients_holder.get(1).ID)

        self.clients_holder.append_client(removed_client)

        self.assertEqual(old_clients_length, len(self.clients_holder.get_all_clients()))

    def test_append_client_changes_a_client_if_already_exists(self):
        client_in_hub = self.clients_holder.get(1)
        client_in_hub.hub_name = "new Name"

        self.clients_holder.append_client(client_in_hub.api_get_real_connected_client())
        new_client = self.clients_holder.get(1)

        self.assertIs(new_client.ID, client_in_hub.api_get_real_connected_client().ID)

    def test_pop_client_removes_a_client_if_exists(self):
        old_clients_length = len(self.clients_holder.get_all_clients())
        removed_client = self.clients_holder.pop_client(self.clients_holder.get(1).ID)

        self.assertEqual(old_clients_length - 1, len(self.clients_holder.get_all_clients()))
        self.assertEqual(removed_client.ID, 1)

    def test_pop_client_returns_none_if_not_exists(self):
        old_clients_length = len(self.clients_holder.get_all_clients())
        removed_client = self.clients_holder.pop_client("non existing ID")

        self.assertEqual(old_clients_length, len(self.clients_holder.get_all_clients()))
        self.assertIsNone(removed_client)
