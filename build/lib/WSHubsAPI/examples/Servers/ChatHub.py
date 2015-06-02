# -*- coding: utf-8 -*-
from WSHubsAPI.Hub import Hub

class ChatHub(Hub):
    def sendToAll(self, name, message):
        #call a client function in a intuitive way
        self.allClients.onMessage(name,message)
        ### we can send to de sender:
        #self.sender.onMessage(str(conn.ID),message)
        ### to all clients but the sender
        #self.otherClients.onMessage(str(conn.ID),message)
        ### or to a selection of clients
        #self.getClients(lambda x:x.ID > 4).onMessage(str(conn.ID),message)

    def getNumOfClientsConnected(self):
        #It is possible to return any kind of object (any no json serializable will be excluded)
        client = self.sender
        return len(client.connections), 'this is a test ñññaá'

