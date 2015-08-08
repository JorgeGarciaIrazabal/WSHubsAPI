import importlib
import os
import time
import unittest
from datetime import datetime, timedelta


class TestThreadPool(unittest.TestCase):
    def setUp(self):
        WSHubsApi = importlib.import_module("client.WSHubsApi")
        self.ws = WSHubsApi.HubsAPI('ws://127.0.0.1:8888/')
        self.ws.connect()

    def tearDown(self):
        try:
            os.removedirs("client")
            self.ws.close()
        except:
            pass

    def test_nonBlocking(self):
        global later,end
        now = datetime.now()
        later = None
        end = False
        def getLater(*args):
            global later,end
            later = datetime.now()
            self.assertTrue(later-now < timedelta(milliseconds=200))
            end = True
        self.ws.BaseHub.server.timeout(0.3)
        self.ws.BaseHub.server.timeout(0).done(getLater)
        while not end and (datetime.now()-now)<timedelta(seconds=2):
            time.sleep(0.1)
        self.assertTrue(end)

    def test_basicObjectSerialization1(self):
        self.assertTrue(self.ws is not None)



if __name__ == '__main__':
    unittest.main()
