# -*- coding: utf-8 -*-
import time

from wshubsapi.hub import Hub


class EchoHub(Hub):
    def echo(self, message):  # _sender is an automatically passed argument
        time.sleep(5)
        return message

