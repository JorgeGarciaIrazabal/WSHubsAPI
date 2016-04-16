# coding=utf-8
import unittest

from wshubsapi.message_separator import MessageSeparator


class TestMessageSeparator(unittest.TestCase):
    def setUp(self):
        self.message_separator = MessageSeparator()

    def tearDown(self):
        pass

    def test_creator__starts_with_buffer_empty_and_with_default_separator(self):
        self.assertEqual(self.message_separator.buffer, "")
        self.assertEqual(self.message_separator.separator, MessageSeparator.DEFAULT_API_SEP)

    def test_add_data__returns_empty_array_anything_if_no_separator_found(self):
        self.assertEqual(self.message_separator.add_data("data to test"), [])

    def test_add_data__returns_one_message_if_ends_with_separator(self):
        received_data = self.message_separator.add_data("message" + self.message_separator.separator)

        self.assertEqual(received_data, ["message"])

    def test_add_data__returns_one_message_if_has_separator_but_does_not_end_with_it(self):
        received_data = self.message_separator.add_data("m" + self.message_separator.separator + "extra m")

        self.assertEqual(received_data, ["m"])

    def test_add_data__returns_concat_old_unfinished_message_in_next_iteration(self):
        self.message_separator.add_data("m" + self.message_separator.separator + "m0")

        received_data = self.message_separator.add_data("m1" + self.message_separator.separator)

        self.assertEqual(received_data, ["m0m1"])

    def test_add_data__can_return_more_than_one_message(self):
        received_data = self.message_separator.add_data("m m0 m1 m2 m3NotEnded".replace(" ", self.message_separator.separator))

        self.assertEqual(received_data, ["m", "m0", "m1", "m2"])

