from wshubsapi.client_in_hub import ClientInHub


class ConnectedClientsGroup(object):
    def __init__(self, connected_clients_in_group, hub_name):
        """
        :type connected_clients_in_group: list of wshubsapi.connected_client.ConnectedClient
        """
        self.hub_name = hub_name
        self.connected_clients = list(map(lambda c: ClientInHub(c, hub_name), connected_clients_in_group))

    def append(self, connected_client):
        """
        :type connected_client: connected_client.ConnectedClient
        """
        self.connected_clients.append(ClientInHub(connected_client, self.hub_name))

    def __getattr__(self, item):
        """
        :rtype: list[Future]
        :param item: function name defined in the client side ("item" name keep because it is a magic function)
        """
        if item.startswith("__") and item.endswith("__"):
            return
        functions = []
        futures = []
        for c in self.connected_clients:
            functions.append(c.__getattr__(item))

        def connection_functions(*args):
            for f in functions:
                futures.append(f(*args))
            return futures

        return connection_functions

    def __getitem__(self, item):
        """
        :rtype : connected_client
        """
        return self.connected_clients.__getitem__(item)

    def __len__(self):
        return len(self.connected_clients)

    def __iter__(self):
        for x in self.connected_clients:
            yield x
