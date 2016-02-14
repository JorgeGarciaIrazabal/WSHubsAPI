from wshubsapi.ClientInHub import ClientInHub


class ConnectedClientsGroup(object):
    def __init__(self, connectedClientsInGroup, hubName):
        """
        :type connectedClientsInGroup: list of wshubsapi.ConnectedClient.ConnectedClient
        """
        self.hubName = hubName
        self.connectedClients = map(lambda c: ClientInHub(c, hubName), connectedClientsInGroup)

    def append(self, connectedClient):
        """
        :type connectedClient: ConnectedClient.ConnectedClient
        """
        self.connectedClients.append(ClientInHub(connectedClient, self.hubName))

    def __getattr__(self, item):
        """
        :param item: function name defined in the client side ("item" name keep because it is a magic function)
        """
        if item.startswith("__") and item.endswith("__"):
            return
        functions = []
        for c in self.connectedClients:
            functions.append(c.__getattr__(item))

        def connectionFunctions(*args):
            for f in functions:
                f(*args)

        return connectionFunctions

    def __getitem__(self, item):
        """
        :rtype : ConnectedClient
        """
        return self.connectedClients.__getitem__(item)

    def __len__(self):
        return self.connectedClients.__len__()

    def __iter__(self):
        for x in self.connectedClients:
            yield x
