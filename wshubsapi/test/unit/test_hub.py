# coding=utf-8
import unittest
from wshubsapi.hub import Hub, UnsuccessfulReplay
from wshubsapi.test.utils.hubs_utils import remove_hubs_subclasses


class TestHub(unittest.TestCase):
    def tearDown(self):
        remove_hubs_subclasses()

    def test_hub_creation__adds__HubName__attribute_to_sub_class(self):
        class TestHub1(Hub):
            pass
        hub = TestHub1()

        self.assertEqual("TestHub1", TestHub1.__HubName__)

        del hub

    def test_construct_unnecessary_replay_returns_unsuccessful_replay_instance(self):
        class TestHub1(Hub):
            pass
        hub = TestHub1()

        unsuccessfulReplay = hub._construct_unsuccessful_replay("replay")

        self.assertIsInstance(unsuccessfulReplay, UnsuccessfulReplay)
        self.assertEqual(unsuccessfulReplay.replay, "replay")


