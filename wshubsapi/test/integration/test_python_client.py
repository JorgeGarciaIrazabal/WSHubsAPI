# coding=utf-8
import unittest
from wshubsapi.test.integration.resources.clients_api.hubs_api import HubsAPI


class TestCommProtocol(unittest.TestCase):
    api = None

    @classmethod
    def setUpClass(cls):
        cls.api = HubsAPI('ws://127.0.0.1:11111/')
        cls.api.connect()

    @classmethod
    def tearDownClass(cls):
        cls.api.ws_client.close()

    def tearDown(self):
        super(TestCommProtocol, self).tearDown()

    def test_echo_responds_same_message(self):
        future = self.api.EchoHub.server.echo("myMessage")

        self.assertEqual(future.result(timeout=1), "myMessage")

    def test_echo_responds_complex_object(self):
        class A(object):
            def __init__(self, name):
                self.name = name

        message = [1, A("myName"), u"ñáñsd"]

        result = self.api.EchoHub.server.echo(message).result(timeout=1)

        self.assertEqual(result[0], 1)
        self.assertEqual(result[1]['name'], "myName")
        self.assertEqual(result[2], u"ñáñsd")

    def test_echo_to_sender__is_called(self):
        self.echo_is_called = False

        def on_echo(message):
            self.assertEqual(message, "testing")
            self.echo_is_called = True

        self.api.EchoHub.client.on_echo = on_echo

        self.api.EchoHub.server.echo_to_sender("testing").result(timeout=1)

        self.assertTrue(self.echo_is_called)
