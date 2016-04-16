# -*- coding: utf-8 -*-
from wshubsapi.hub import Hub


class EchoHub(Hub):
    @staticmethod
    def echo(message):
        return message

    @staticmethod
    def echo_to_sender(message, _sender):
        _sender.on_echo(message)



