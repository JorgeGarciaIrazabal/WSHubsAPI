import logging
import time

from WSFunctionProtocol.HubDecorator import  HubDecorator

log = logging.getLogger(__name__)

class returnClass:
    def __init__(self):
        self.a = 10
        self.b =20

@HubDecorator.hub
class Hub1:
    def test(self, _client, a=1, b=2):
        print(b)
        time.sleep(b)
        return a, b

    def tast(self, _client, a=5, b=1, c=3):
        print(a, b)

@HubDecorator.hub
class Hub2:
    def test(self, _client, a=1, b=2):
        print(a, b)

    def tast(self, _client, a=5, b=1, c=3):
        """
        @type _client: MessageHandler
        """
        _client.onTest(5,6)
        return returnClass()

