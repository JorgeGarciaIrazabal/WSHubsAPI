# -*- coding: utf-8 -*-
from wshubsapi.hub import Hub


class ChatHub(Hub):
    def send_to_all(self, name, _sender, message="hello"):  # _sender is an automatically passed argument
        other_clients = self.clients.get_other_clients(_sender)
        if len(other_clients) > 0:
            other_clients.on_message(name, message)
        return len(other_clients)

    def send_message_to_client(self, message, client_id):
        self.clients.get_client(client_id).on_message(message)

    @staticmethod
    def raise_exception(exception_message):
        raise Exception(exception_message)
