# -*- coding: utf-8 -*-
from wshubsapi.Hub import Hub


class ChatHub(Hub):
    def sendToAll(self, name, _sender, message="hello"):  # _sender is an automatically passed argument
        otherClients = self._getClientsHolder().getOtherClients(_sender)
        if len(otherClients) > 0:
            futures = otherClients.onMessage(name, message)
            print futures[0].result()
        return len(otherClients)

    @staticmethod
    def staticFunc():
        pass

    @classmethod
    def classMethod(cls):
        pass
