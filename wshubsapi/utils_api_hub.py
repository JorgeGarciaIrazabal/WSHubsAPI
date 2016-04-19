# -*- coding: utf-8 -*-
from wshubsapi.hub import Hub
from wshubsapi.hubs_inspector import HubsInspector


class UtilsAPIHub(Hub):
    def set_id(self, client_id, _sender):
        connections = self.clients.all_connected_clients
        if client_id in connections:
            raise Exception("new ID already in use")
        connections.pop(_sender.ID)
        _sender.ID = client_id
        connections[client_id] = _sender.api_get_real_connected_client()

    @staticmethod
    def get_id(_sender):
        return _sender.ID

    def is_client_connected(self, client_id):
        return client_id in self.clients.all_connected_clients

    @staticmethod
    def get_hubs_structure():
        return HubsInspector.get_hubs_information()
