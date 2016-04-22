import datetime

import jsonpickle

import wshubsapi.comm_environment
from wshubsapi import utils
import json
import unittest


class ComplexObject(object):
    def __init__(self):
        self.a = self


class TestSerialization(unittest.TestCase):
    def setUp(self):
        self.serialization_args = dict()
        utils.set_serializer_date_handler()

    def test_basicObjectSerialization(self):
        serialization = utils.serialize_message(self.serialization_args, 5)
        self.assertTrue(serialization == '5', 'number serialization')
        serialization = utils.serialize_message(self.serialization_args, "hi")
        self.assertTrue(serialization == '"hi"', 'str serialization')

    def test_simpleObjects(self):
        class SimpleObject(object):
            def __init__(self):
                self.a = 1
                self.b = "hi"

        serialization = utils.serialize_message(self.serialization_args, SimpleObject())
        self.assertTrue(json.loads(serialization)["a"] == 1)
        self.assertTrue(json.loads(serialization)["b"] == "hi")

    def test_complexObjects(self):
        class ComplexObject(object):
            def __init__(self):
                self.a = {"a": 10, 1: 15}
                self.b = [1, 2, "hola"]

        serialization = utils.serialize_message(self.serialization_args, ComplexObject())
        serObject = json.loads(serialization)
        self.assertTrue(isinstance(serObject["a"], dict))
        self.assertTrue(serObject["a"]["a"] == 10)
        self.assertTrue(serObject["a"]["1"] == 15)
        self.assertTrue(len(serObject["b"]) == 3)

    def test_cycleRef(self):
        serialization = jsonpickle.encode(ComplexObject())
        serObject = jsonpickle.decode(serialization)
        self.assertEqual(serObject.a, serObject)

    def test_dateTimeObjects(self):
        date = datetime.datetime.now()
        serialization = utils.serialize_message(self.serialization_args, {"datetime": date})
        self.assertTrue(json.loads(serialization)["datetime"] == date.strftime(utils.DATE_TIME_FORMAT),
                        'datetime serialization')

        date = datetime.date(2001, 1, 1)
        serialization = utils.serialize_message(self.serialization_args, {"datetime": date})
        self.assertTrue(json.loads(serialization)["datetime"] == date.strftime(utils.DATE_TIME_FORMAT),
                        'datetime serialization')

        date = datetime.time()
        serialization = utils.serialize_message(self.serialization_args, {"datetime": date})
        self.assertTrue(json.loads(serialization)["datetime"] == date.strftime(utils.DATE_TIME_FORMAT),
                        'datetime serialization')

