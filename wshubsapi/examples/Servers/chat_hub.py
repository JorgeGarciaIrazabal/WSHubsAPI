# -*- coding: utf-8 -*-
from wshubsapi.hub import Hub


class ChatHub(Hub):
    def send_to_all(self, name, _sender, message="hello"):  # _sender is an automatically passed argument
        other_clients = self.clients.get_other_clients(_sender)
        if len(other_clients) > 0:
            other_clients.print_message(name, message)
        return len(other_clients)

    def _define_client_functions(self):
        """
        This function will tell the client possible client functions to be called from sever
        It is just to inform, it is not mandatory but recommended
        """
        return dict(print_message=lambda sender_name, msg: None)
