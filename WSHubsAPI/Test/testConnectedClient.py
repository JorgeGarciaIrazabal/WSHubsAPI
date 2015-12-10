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
