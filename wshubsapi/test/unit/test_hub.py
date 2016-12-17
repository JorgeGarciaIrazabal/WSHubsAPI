# coding=utf-8
import unittest

from flexmock import flexmock

from wshubsapi.connected_clients_holder import ConnectedClientsHolder
from wshubsapi.comm_environment import CommEnvironment
from wshubsapi.client_in_hub import ClientInHub
from wshubsapi.connected_client import ConnectedClient
from wshubsapi.hub import Hub, UnsuccessfulReplay
from wshubsapi.test.utils.hubs_utils import remove_hubs_subclasses


class TestHub(unittest.TestCase):
    def setUp(self):
        class TestHub1(Hub):
            pass
        self.hub = TestHub1()
        connected_client_sender = flexmock(ConnectedClient(CommEnvironment(), None), ID="myId")
        self.sender = ClientInHub(connected_client_sender, TestHub1.__HubName__)

    def tearDown(self):
        del self.hub
        remove_hubs_subclasses()

    def test_hub_creation__adds__HubName__attribute_to_sub_class(self):
        self.assertEqual("TestHub1", self.hub.__HubName__)

    def test_construct_unnecessary_replay_returns_unsuccessful_replay_instance(self):
        unsuccessful_replay = self.hub._construct_unsuccessful_replay("reply")

        self.assertIsInstance(unsuccessful_replay, UnsuccessfulReplay)
        self.assertEqual(unsuccessful_replay.reply, "reply")

    def test_hub_creation_starts_with_no_subscribed_clients(self):

        self.assertEqual(len(self.hub.get_subscribed_clients_ids()), 0)

    def test_subscribe_to_hub_append_sender_to_hub_subscribes_and_returns_true(self):
        self.assertTrue(self.hub.subscribe_to_hub(self.sender))

        subscribed_clients_ids = self.hub.get_subscribed_clients_ids()

        self.assertEqual(subscribed_clients_ids[0], self.sender.ID)

    def test_subscribe_to_hub_does_not_subscribes_client_if_already_exist_and_returns_false(self):
        self.hub.subscribe_to_hub(self.sender)

        self.assertFalse(self.hub.subscribe_to_hub(self.sender))

        subscribed_clients_ids = self.hub.get_subscribed_clients_ids()
        self.assertEqual(len(subscribed_clients_ids), 1)

    def test_unsubscribe_from_hub_remove_sender_to_hub_subscribes_and_returns_true(self):
        self.hub.subscribe_to_hub(self.sender)
        self.assertTrue(self.hub.unsubscribe_from_hub(self.sender))
        self.assertEqual(len(self.hub.get_subscribed_clients_ids()), 0)

    def test_unsubscribe_from_hub_does_not_remove_sender_if_not_exists_and_returns_false(self):
        self.hub.subscribe_to_hub(self.sender)
        self.assertFalse(self.hub.unsubscribe_from_hub(flexmock(api_get_real_connected_client=lambda: "hello")))
        self.assertEqual(len(self.hub.get_subscribed_clients_ids()), 1)

    def test_get_subscribed_clients_returns_the_right_clients(self):
        def construct_sender(id_):
            connected_client_sender = flexmock(ConnectedClient(CommEnvironment(), None), ID=id_)
            return ClientInHub(connected_client_sender, self.hub.__HubName__)

        client_a = construct_sender("a")
        client_b = construct_sender("b")
        client_c = construct_sender("c")
        self.assertEqual(len(self.hub.get_subscribed_clients_ids()), 0)
        self.hub.subscribe_to_hub(client_a)
        self.assertEqual(self.hub.get_subscribed_clients_ids()[0], "a")
        self.hub.subscribe_to_hub(client_b)
        self.assertEqual(self.hub.get_subscribed_clients_ids()[1], "b")
        self.hub.subscribe_to_hub(client_c)
        self.assertEqual(self.hub.get_subscribed_clients_ids()[2], "c")

    def test_clients_return_clients_holder(self):
        self.assertIsInstance(self.hub.clients, ConnectedClientsHolder)

    def test_clients_can_not_be_set(self):
        def set_clients():
            self.hub.clients = 10

        self.assertRaises(AttributeError, set_clients)
