# coding=utf-8
import unittest
from wshubsapi.hub import Hub, HubError, UnsuccessfulReplay
from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.Test.utils.HubsUtils import removeHubsSubclasses


class TestHub(unittest.TestCase):
    def tearDown(self):
        removeHubsSubclasses()

    def test_HubCreation_insertsInstanceInHUBs_DICT(self):
        class TestHub1(Hub):
            pass
        hub = TestHub1()

        self.assertTrue(hub in HubsInspector.HUBS_DICT.values())

        del hub

    def test_HubCreation_Adds__HubName__AttributeToSubClass(self):
        class TestHub1(Hub):
            pass
        hub = TestHub1()

        self.assertEqual("TestHub1", TestHub1.__HubName__)

        del hub

    def test_HubCreation_InsertDefined__HubName__InHUBs_DICT(self):
        class TestHub1(Hub):
            __HubName__ = "newValue"
            pass
        hub = TestHub1()

        self.assertEqual("newValue", list(HubsInspector.HUBS_DICT.keys())[0])

        del hub

    def test_HubCreation_RaisesExceptionIfCreatedMoreThatOneInstanceOfHub(self):
        class TestHub1(Hub):
            pass
        hub = TestHub1()

        self.assertRaises(HubError, TestHub1)

        del hub

    def test_HubCreation_RaisesExceptionIfClassNameStartsWith__(self):
        class __TestHub1(Hub):
            pass

        self.assertRaises(HubError, __TestHub1)

    def test_HubCreation_RaisesExceptionIfClassNameIsWsClient(self):
        class wsClient(Hub):
            pass

        self.assertRaises(HubError, wsClient)

    def test_ConstructUnsuccessfulReplay_returnsUnsuccessfulReplayInstance(self):
        class TestHub1(Hub):
            pass
        hub = TestHub1()

        unsuccessfulReplay = hub._construct_unsuccessful_replay("replay")

        self.assertIsInstance(unsuccessfulReplay, UnsuccessfulReplay)
        self.assertEqual(unsuccessfulReplay.replay, "replay")


