from WSHubsAPI.Hub import Hub, HubException

import unittest

class TestHubDetection(unittest.TestCase):
    def setUp(self):
        #Constucting hubs for testing
        class TestHub(Hub):
            def getData(self):
                pass

        class TestHub2(Hub):
            pass

        Hub.initHubsInspection()

    def test_hubsInspection(self):
        self.assertEqual(len(Hub.HUBs_DICT), 2, 'Detects all Hubs')
        self.assertTrue(issubclass(Hub.HUBs_DICT['TestHub'].__class__, Hub), 'Hubs subclass is class')
        self.assertTrue(issubclass(Hub.HUBs_DICT['TestHub2'].__class__, Hub), 'Hubs subclass is class')
        self.assertTrue(getattr(Hub.HUBs_DICT['TestHub'], "getData"), 'Detects function')

    def test_hubsLimitations(self):
        class TestHubLimitation(Hub):
            pass

        class TestHubLimitation2(Hub):
            __HubName__ = "TestHubLimitation"

        self.assertRaises(HubException, Hub.initHubsInspection, forceReconstruction=True)
        TestHubLimitation2.__HubName__ = "TestHubLimitation2"

        class TestHubLimitation3(Hub):
            def __init__(self, aux):
                super(TestHubLimitation3, self).__init__()


        self.assertRaises(HubException, Hub.initHubsInspection, forceReconstruction=True)
        TestHubLimitation3.__init__ = lambda : 1+1

    def test_hubsLimitations_startWithUnderscores(self):
        class __TestHubLimitation(Hub):
            pass

        self.assertRaises(HubException, Hub.initHubsInspection, forceReconstruction=True)

    def test_hubsLimitations_wsClient(self):
        class wsClient(Hub):
            pass

        self.assertRaises(HubException, Hub.initHubsInspection, forceReconstruction=True)

if __name__ == '__main__':
    unittest.main()
