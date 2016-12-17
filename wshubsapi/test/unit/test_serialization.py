import datetime
from datetime import timedelta
import json
import unittest

from wshubsapi.comm_environment import CommEnvironment
from wshubsapi.serializer import Serializer


class ComplexObject(object):
    def __init__(self):
        self.a = self


class TestSerialization(unittest.TestCase):
    def setUp(self):
        self.serializer = Serializer()
        self.comm_env = CommEnvironment()

    def test_basicObjectSerialization(self):
        serialization = self.comm_env.serialize_message(5)
        self.assertTrue(serialization == '5', 'number serialization')
        serialization = self.comm_env.serialize_message("hi")
        self.assertTrue(serialization == '"hi"', 'str serialization')

    def test_simpleObjects(self):
        class SimpleObject(object):
            def __init__(self):
                self.a = 1
                self.b = "hi"

        serialization = self.comm_env.serialize_message(SimpleObject())
        self.assertTrue(json.loads(serialization)["a"] == 1)
        self.assertTrue(json.loads(serialization)["b"] == "hi")

    def test_complexObjects(self):
        class ComplexObject(object):
            def __init__(self):
                self.a = {"a": 10, 1: 15}
                self.b = [1, 2, "hello"]

        serialization = self.comm_env.serialize_message(ComplexObject())
        ser_obj = json.loads(serialization)
        self.assertTrue(isinstance(ser_obj["a"], dict))
        self.assertTrue(ser_obj["a"]["a"] == 10)
        self.assertTrue(ser_obj["a"]["1"] == 15)
        self.assertTrue(len(ser_obj["b"]) == 3)

    def test_cycleRef(self):
        serialization = self.comm_env.serialize_message(ComplexObject())
        ser_obj = json.loads(serialization)
        checking_obj = ser_obj
        for i in range(self.comm_env.serializer.max_depth):
            self.assertIn('a', checking_obj)
            checking_obj = checking_obj['a']
        self.assertNotIn('a', checking_obj)

    def test_dateTimeObjects(self):
        date = datetime.datetime.now()
        serialization = self.comm_env.serialize_message({"datetime": date})
        self.assertIn(Serializer.DATE_TAME_KEY, serialization)
        datetime_obj = self.serializer.unserialize(serialization)
        self.assertIsInstance(datetime_obj['datetime'], datetime.datetime)
        print(datetime.datetime.now() - datetime_obj['datetime'])
        self.assertTrue(datetime.datetime.now() - datetime_obj['datetime'] < timedelta(milliseconds=25))

