from wshubsapi.connected_clients_group import ConnectedClientsGroup

class ConnectedClientsHolder:
    all_connected_clients = dict()

    def __init__(self, hub_instance):
        self.hub_instance = hub_instance
        self.hub_name = self.hub_instance.__class__.__HubName__

    def get_all_clients(self):
        return ConnectedClientsGroup(list(self.all_connected_clients.values()), self.hub_name)

    def get_other_clients(self, sender):
        """
        :type sender: ConnectedClientsGroup
        """
        connected_clients = [c for c in self.all_connected_clients.values() if c.ID != sender.ID]
        return ConnectedClientsGroup(connected_clients, self.hub_instance)

    def get_clients(self, filter_function):
        return ConnectedClientsGroup(filter(filter_function, self.all_connected_clients.values()), self.hub_instance)

    def get_client(self, client_id):
        return ConnectedClientsGroup([self.all_connected_clients[client_id]], self.hub_instance)[0]

    def get(self, filter_criteria):
        """
        smart function that will retrieve clients depending on the filter criteria type
        :param filter_criteria: - if list of IDs,  returns the clients with the matching IDs
                                - if ID, returns the client with the matching ID
                                - if function, filter all clients with the specified function
        :return: ClientInHub or ConnectedClientsGroup
        """
        if isinstance(filter_criteria, (list, tuple)):
            return self.get_clients(lambda x: x.ID in filter_criteria)
        elif hasattr(filter_criteria, '__call__'):
            return self.get_clients(filter_criteria)
        else:
            return self.get_client(filter_criteria)

    def get_subscribed_clients(self):
        subscribed_clients = self.hub_instance.get_subscribed_clients_to_hub()
        return ConnectedClientsGroup([self.all_connected_clients[ID] for ID in subscribed_clients], self.hub_instance)

    @classmethod
    def append_client(cls, client):
        cls.all_connected_clients[client.ID] = client

    @classmethod
    def pop_client(cls, client_id):
        """
        :type client_id: str|int
        """
        return cls.all_connected_clients.pop(client_id, None)


