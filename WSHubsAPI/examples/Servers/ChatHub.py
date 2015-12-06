# -*- coding: utf-8 -*-
import time

from WSHubsAPI.Hub import Hub

class ChatHub(Hub):
    def sendToAll(self, name, message, _sender): #_sender is an automatically passed argument
        ### we can call a sender's function in a intuitive way (the function has to be defined in the client):
        #_sender.onMessage(name,message)
        ###call function from all clients
        #self.allClients.onMessage(name,message)
        ###call function from all clients but the sender
        otherClients = self._clientsHolder.getOtherClients(_sender)
        otherClients.onMessage(name, message)
        ### or call function from a selection of clients
        #self.getClients(lambda x:x.ID > 4).onMessage(name,message)
        return len(otherClients)

    def getNumOfClientsConnected(self):
        #It is possible to return any kind of object (any no json serializable will be excluded)
        client = self.sender
        return len(client.connections), 'this is a test'

