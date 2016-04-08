# coding=utf-8
from flexmock import flexmock, flexmock_teardown

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
        flexmock(CommEnvironment, __check_futures=lambda *args: None)
        self.comm_environment = CommEnvironment(max_workers=0, unprovided_id_template="unprovided_{}")

    def tearDown(self):
        flexmock_teardown()
        super(TestCommProtocol, self).tearDown()

    def test_construct_initializeMandatoryAttributes(self):
        self.assertIsInstance(self.comm_environment.message_received_queue, MessagesReceivedQueue)
        self.assertIsInstance(self.comm_environment.lock, thread.LockType)
        self.assertIs(self.comm_environment.all_connected_clients, ConnectedClientsHolder.all_connected_clients)

    def test_getUnprovidedID_returnsFirstAvailableUnprovidedID(self):
        firstClient = ConnectedClient(self.comm_environment, lambda x: x)
        secondClient = ConnectedClient(self.comm_environment, lambda x: x)
        self.comm_environment.on_opened(firstClient)  # first UnprovidedID = unprovided_0
        self.comm_environment.on_opened(secondClient)  # first UnprovidedID = unprovided_1

        unprovidedId = self.comm_environment.get_unprovided_id()

        self.assertEqual(unprovidedId, "unprovided_2")

    def test_getUnprovidedID_returnAvailableUnprovidedIdsIfExist(self):
        self.comm_environment.available_unprovided_ids.append("availableId_1")

        unprovidedId = self.comm_environment.get_unprovided_id()

        self.assertEqual(unprovidedId, "availableId_1")

    def test_getUnprovidedID_availableIdsAreRemovedWhenUsed(self):
        self.comm_environment.available_unprovided_ids.append("availableId_1")
        unprovidedId1 = self.comm_environment.get_unprovided_id()
        unprovidedId2 = self.comm_environment.get_unprovided_id()

        self.assertEqual(unprovidedId2, "unprovided_0")
