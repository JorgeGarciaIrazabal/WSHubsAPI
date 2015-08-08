import datetime
from wshubsapi import utils
from wshubsapi.CommProtocol import CommHandler
import json
import unittest

class TestSerialization(unittest.TestCase):
    def setUp(self):
        self.commHandler = CommHandler()
        utils.setSerializerDateTimeHandler()

    def test_basicObjectSerialization(self):
        serialization = self.commHandler.serializeMessage(5)
        self.assertTrue(serialization == '5', 'number serialization')
        serialization = self.commHandler.serializeMessage("hi")
        self.assertTrue(serialization == '"hi"', 'str serialization')

    def test_simpleObjects(self):
        class SimpleObject(object):
            def __init__(self):
                self.a = 1
                self.b = "hi"

        serialization = self.commHandler.serializeMessage(SimpleObject())
        self.assertTrue(json.loads(serialization)["a"] == 1)
        self.assertTrue(json.loads(serialization)["b"] == "hi")

    def test_complexObjects(self):
        class ComplexObject(object):
            def __init__(self):
                self.a = {"a":10,1:15}
                self.b = [1,2,"hola"]

        serialization = self.commHandler.serializeMessage(ComplexObject())
        serObject = json.loads(serialization)
        self.assertTrue(isinstance(serObject["a"],dict))
        self.assertTrue(serObject["a"]["a"] == 10)
        self.assertTrue(serObject["a"]["1"] == 15)
        self.assertTrue(len(serObject["b"]) == 3)

    def test_cycleRef(self):
        class ComplexObject(object):
            def __init__(self):
                self.a = self

        serialization = self.commHandler.serializeMessage(ComplexObject())
        serObject = json.loads(serialization)
        self.assertTrue("ComplexObject" in serObject["a"])

    def test_dateTimeObjects(self):
        date = datetime.datetime.now()
        serialization = self.commHandler.serializeMessage({"datetime":date})
        self.assertTrue(json.loads(serialization)["datetime"] == date.strftime(utils.DATE_TIME_FORMAT), 'datetime serialization')

        date = datetime.date(2001,1,1)
        serialization = self.commHandler.serializeMessage({"datetime":date})
        self.assertTrue(json.loads(serialization)["datetime"] == date.strftime(utils.DATE_TIME_FORMAT), 'datetime serialization')

        date = datetime.time()
        serialization = self.commHandler.serializeMessage({"datetime":date})
        self.assertTrue(json.loads(serialization)["datetime"] == date.strftime(utils.DATE_TIME_FORMAT), 'datetime serialization')

if __name__ == '__main__':
    unittest.main()
