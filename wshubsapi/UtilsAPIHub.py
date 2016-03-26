# -*- coding: utf-8 -*-
from wshubsapi.Hub import Hub
from wshubsapi.HubsInspector import HubsInspector


class UtilsAPIHub(Hub):
    def setId(self, clientId, _sender):
        connections = self._getClientsHolder().allConnectedClientsDict
        connections.pop(_sender.ID)
        _sender.ID = clientId
        connections[clientId] = _sender.api_getRealConnectedClient()
        return True

    def getId(self, _sender):
        return _sender.ID

    def isClientConnected(self, clientId):
        return clientId in self._getClientsHolder().allConnectedClientsDict

    def getHubsStructure(self):
        return HubsInspector.getHubsInformation()
