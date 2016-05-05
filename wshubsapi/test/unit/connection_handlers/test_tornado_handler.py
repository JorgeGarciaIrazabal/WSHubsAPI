# coding=utf-8
import unittest

import tornado.web
from flexmock import flexmock, flexmock_teardown

from wshubsapi.comm_environment import CommEnvironment
from wshubsapi.connection_handlers.tornado_handler import ConnectionHandler


class TestTornadoHandler(unittest.TestCase):
    def setUp(self):
        CommEnvironment.get_instance(max_workers=0)
        app = self.get_app()
        connection = flexmock(set_close_callback=lambda *args: None)
        request = tornado.web._RequestDispatcher(app, connection)
        self.connection_handler = ConnectionHandler(app, request)

    def get_app(self):
        self.app = tornado.web.Application([
            (r'/path/to/websocket', ConnectionHandler)
        ])
        return self.app

    def tearDown(self):
        del self.connection_handler.comm_environment.message_received_queue
        flexmock_teardown()

