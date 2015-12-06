# coding=utf-8
import unittest
from WSHubsAPI.utils import *


class TestUtils(unittest.TestCase):
	def test_ASCII_UpperCaseIsInitialized(self):
		randomExistingLetters = ["A", "Q", "P"]
		for letter in randomExistingLetters:
			self.assertIn(letter, ASCII_UpperCase, "letter in ASCII_UpperCase")

	def test_ASCII_UpperCaseDoesNotContainNotASCIICharacters(self):
		nonASCII_letter = "Ñ"
		self.assertNotIn(nonASCII_letter, ASCII_UpperCase)

	def test_getArgsReturnsAllArgumentsInMethod(self):
		testCases = [
			{"method": lambda x, y, z: x, "expected": ["x", "y", "z"]},
			{"method": lambda y=2, z=1: y, "expected": ["y", "z"]},
			{"method": lambda: 1, "expected": []},
			{"method": lambda x, self, cls, _sender: x, "expected": ["x"]},
			{"method": lambda x, self, _sender: x, "expected": ["x"]},
		]
		for case in testCases:
			returnedFromFunction = getArgs(case["method"])

			self.assertEqual(returnedFromFunction, case["expected"])

	def test_getDefaultsReturnsTheDefaultValues(self):
		testCases = [
			{"method": lambda x, y, z: x, "expected": []},
			{"method": lambda y=2, z="a": y, "expected": [2, '"a"']},
			{"method": lambda x, y=4, z="ñoño": 1, "expected": [4, '"ñoño"']},
		]
		for case in testCases:
			returnedFromFunction = getDefaults(case["method"])

			self.assertEqual(returnedFromFunction, case["expected"])
