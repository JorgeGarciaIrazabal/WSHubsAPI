# -*- coding: utf-8 -*-
from wshubsapi.Hub import Hub
from wshubsapi.HubsInspector import HubsInspector


class UtilAPIHub(Hub):
    def setId(self, clientId, _sender):
        connections = self.getClientsHolder().allConnectedClientsDict
        connections.pop(_sender[0].ID)
        _sender.ID = clientId
        connections[clientId] = _sender
        return True

    def getId(self, _sender):
        return _sender[0].ID

    def isClientConnected(self, clientId):
        return clientId in self.getClientsHolder().allConnectedClientsDict

    def getHubsStructure(self):
        return HubsInspector.getHubsInformation()
