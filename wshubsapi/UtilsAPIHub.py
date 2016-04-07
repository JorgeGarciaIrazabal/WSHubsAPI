# -*- coding: utf-8 -*-
from wshubsapi.Hub import Hub
from wshubsapi.HubsInspector import HubsInspector


class UtilsAPIHub(Hub):
    def set_id(self, client_id, _sender):
        connections = self._getClientsHolder().allConnectedClientsDict
        connections.pop(_sender.ID)
        _sender.ID = client_id
        connections[client_id] = _sender.api_getRealConnectedClient()
        return True

    @staticmethod
    def get_id(_sender):
        return _sender.ID

    def is_client_connected(self, client_id):
        return client_id in self._getClientsHolder().allConnectedClientsDict

    @staticmethod
    def get_hubs_structure():
        return HubsInspector.getHubsInformation()
