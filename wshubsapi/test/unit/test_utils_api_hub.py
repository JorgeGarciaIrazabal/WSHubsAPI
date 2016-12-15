# coding=utf-8
import unittest

from flexmock import flexmock, flexmock_teardown

from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.connected_client import ConnectedClient
from wshubsapi.client_in_hub import ClientInHub
from wshubsapi.comm_environment import CommEnvironment
from wshubsapi.connected_clients_holder import ConnectedClientsHolder
from wshubsapi.test.utils.hubs_utils import remove_hubs_subclasses
from wshubsapi.utils_api_hub import UtilsAPIHub


class TestUtilsApiHub(unittest.TestCase):
    def setUp(self):
        self.utils_hub = UtilsAPIHub()
        self.clients_holder = ConnectedClientsHolder(self.utils_hub)
        ConnectedClientsHolder.all_connected_clients = dict()

        for i in range(2):
            connected_client = flexmock(ConnectedClient(CommEnvironment(), None))
            connected_client.ID = i
            self.clients_holder.append_client(connected_client)
        connected_client_sender = flexmock(ConnectedClient(CommEnvironment(), None), ID=-1)
        self.clients_holder.append_client(connected_client_sender)
        self.sender = ClientInHub(connected_client_sender, UtilsAPIHub.__HubName__)

    def tearDown(self):
        flexmock_teardown()
        remove_hubs_subclasses()

    def test_set_id__change_id_of_sender_and_from_all_connected_clients(self):
        self.utils_hub.set_id(10, self.sender)

        self.assertEqual(self.sender.ID, 10)
        self.assertNotIn(-1, ConnectedClientsHolder.all_connected_clients)
        self.assertIn(10, ConnectedClientsHolder.all_connected_clients)

    def test_set_id__raises_exception_if_id_already_exist(self):
        self.assertRaises(Exception, self.utils_hub.set_id, 1, self.sender)

    def test_get_id__returns_senderID(self):
        self.assertEqual(self.utils_hub.get_id(self.sender), -1)

    def test_is_client_connected_returns_true_if_it_is_connected(self):
        self.assertTrue(self.utils_hub.is_client_connected(0))

    def test_is_client_connected_returns_false_if_not_connected(self):
        self.assertFalse(self.utils_hub.is_client_connected(999))

    def test_get_hubs_structure_returns_HubsInspector_get_hubs_information(self):
        self.assertEqual(self.utils_hub.get_hubs_structure(), HubsInspector.get_hubs_information())

