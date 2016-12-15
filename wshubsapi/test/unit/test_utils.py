# coding=utf-8
import unittest

from flexmock import flexmock, flexmock_teardown

from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.utils import *


class TestUtils(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        flexmock_teardown()

    def test_ascii__upper_case_is_initialized(self):
        random_letters = ["A", "Q", "P"]
        for letter in random_letters:
            self.assertIn(letter, ASCII_UpperCase, "letter in ASCII_UpperCase")

    def test_ascii__upper_case_does_not_contain_not_ascii_characters(self):
        non_ascii_letter = "Ñ"
        self.assertNotIn(non_ascii_letter, ASCII_UpperCase)

    def test_get_ags_returns_all_arguments_in_method(self):
        class AuxClass:
            def aux_func(self, x, y, z):
                pass

            @staticmethod
            def aux_static(self, x, y):
                pass

            @classmethod
            def aux_class_method(cls, x, y):
                pass

        test_cases = [
            {"method": lambda x, y, z: x, "expected": ["x", "y", "z"]},
            {"method": lambda y=2, z=1: y, "expected": ["y", "z"]},
            {"method": lambda: 1, "expected": []},
            {"method": AuxClass().aux_func, "expected": ["x", "y", "z"]},
            {"method": AuxClass.aux_static, "expected": ["self", "x", "y"]},
            {"method": AuxClass.aux_class_method, "expected": ["x", "y"]}
        ]
        for case in test_cases:
            returned_from_function = get_args(case["method"])

            self.assertEqual(returned_from_function, case["expected"])

    def test_get_defaults_returns_the_default_values(self):
        test_cases = [
            {"method": lambda x, y, z: x, "expected": []},
            {"method": lambda y=2, z="a": y, "expected": [2, '"a"']},
            {"method": lambda x, y=4, z="ñoño": 1, "expected": [4, '"ñoño"']},
        ]
        for case in test_cases:
            returned_from_function = get_defaults(case["method"])

            self.assertEqual(returned_from_function, case["expected"])

    def test_is_function_for_ws_client_includes_standard_function(self):
        def this_is_a_new_function(test):
            print(test)

        self.assertTrue(is_function_for_ws_client(this_is_a_new_function), "new function is detected")

    def test_is_function_for_ws_client__excludes_protected_and_private_functions(self):
        def _this_is_a_protected_function(test):
            print(test)

        def __this_is_a_private_function(test):
            print(test)

        self.assertFalse(is_function_for_ws_client(_this_is_a_protected_function), "protected function is excluded")
        self.assertFalse(is_function_for_ws_client(__this_is_a_private_function), "private function is excluded")

    def test_is_function_for_ws_client_excludes_already_existing_functions(self):
        self.assertFalse(is_function_for_ws_client(HubsInspector.HUBS_DICT), "excludes existing functions")

    def test_get_module_path_returns_test_utils_py_module_path(self):
        self.assertIn("wshubsapi" + os.sep + "test", get_module_path())
