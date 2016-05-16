from SimpleHTTPServer import SimpleHTTPRequestHandler
import logging
import threading

import requests
import tornado
from concurrent.futures import Future
from tornado import web

from wshubsapi.connected_client import ConnectedClient
from wshubsapi.comm_environment import CommEnvironment

__author__ = 'Jorge'
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class SimpleRequestHandler(SimpleHTTPRequestHandler):
    def setup(self):
        SimpleHTTPRequestHandler.setup(self)
        self._connected_client_mock = ConnectedClient(self.comm_environment, self.write_message)
        self.comm_environment = CommEnvironment.get_instance()

    def __get_body(self):
        content_len = int(self.headers.getheader('content-length', 0))
        return self.rfile.read(content_len)

    def write_message(self, message):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(message)
        self.wfile.close()

    def do_GET(self):
        message = self.__get_body()
        log.debug("request received: \n{} ".format(message))
        self.comm_environment.on_message(self._connected_client_mock, message)
        # SimpleHTTPRequestHandler.do_GET(self)


class TornadoRequestHandler(tornado.web.RequestHandler):
    comm_environment = None

    def data_received(self, chunk):
        pass

    def __init__(self, application, request, **kwargs):
        super(TornadoRequestHandler, self).__init__(application, request, **kwargs)
        self._connected_client_mock = ConnectedClient(self.comm_environment, self.write)
        if TornadoRequestHandler.comm_environment is None:
            TornadoRequestHandler.comm_environment = CommEnvironment()

    def get(self, *args):
        message = self.request.body
        log.debug("Message received from:\n{} ".format(message))
        self.comm_environment.on_message(self._connected_client_mock, message)


class DjangoRequestHandler:
    comm_environment = None

    def __init__(self):
        self._connected_client_mock = ConnectedClient(self.comm_environment, self.get_response)
        if DjangoRequestHandler.comm_environment is None:
            DjangoRequestHandler.comm_environment = CommEnvironment()
        self.response = ""

    def get_response(self, msg):
        self.response = msg

    def request_handler(self, request):
        from django.http import HttpResponse  # this could not necessary if imported at top
        message = request.body
        self.comm_environment.onMessage(self._connected_client_mock, message)
        return HttpResponse(self.response)


class RequestClient:
    def __init__(self, url):
        self.url = url

    def connect(self):
        pass  # necessary function but it doesn't have to do any thing

    def send(self, msg_str):
        future = Future()

        def request():
            result = requests.get(self.url, data=msg_str).json()
            if result['success']:
                future.set_result(result['reply'])
            else:
                future.set_exception(result['reply'])

        threading.Thread(target=request).start()  # todo use a thread pool
        return future
