# -*- coding: utf-8 -*-
from wshubsapi.hub import Hub


class ChatHub(Hub):
    def send_to_all(self, name, _sender, message="hello"):  # _sender is an automatically passed argument
        other_clients = self._get_clients_holder().get_other_clients(_sender)
        if len(other_clients) > 0:
            other_clients.on_message(name, message)
        return len(other_clients)

    @staticmethod
    def static_func():
        pass

    @classmethod
    def class_method(cls):
        pass
