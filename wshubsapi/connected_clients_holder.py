from wshubsapi.connected_clients_group import ConnectedClientsGroup


class ConnectedClientsHolder:
    all_connected_clients = dict()

    def __init__(self, hub_instance):
        """
        :type hub_instance: wshubsapi.hub.Hub
        """
        self.hub_instance = hub_instance
        self.hub_name = self.hub_instance.__class__.__HubName__
        self.hub_subscribers = []

    def get_all_clients(self):
        return ConnectedClientsGroup(list(self.all_connected_clients.values()), self.hub_name)

    def get_other_clients(self, sender):
        """
        :type sender: wshubsapi.client_in_hub.ClientInHub
        """
        connected_clients = [c for c in self.all_connected_clients.values() if c.ID != sender.ID]
        return ConnectedClientsGroup(connected_clients, self.hub_name)

    def get_clients(self, filter_function):
        clients = filter(filter_function, self.all_connected_clients.values())
        return ConnectedClientsGroup(list(clients), self.hub_name)

    def get_client(self, client_id):
        """
        :rtype: wshubsapi.client_in_hub.ClientInHub
        """
        return ConnectedClientsGroup([self.all_connected_clients[client_id]], self.hub_name)[0]

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
        self.hub_subscribers = list(filter(lambda c: not c.api_is_closed, self.hub_subscribers))
        return ConnectedClientsGroup(self.hub_subscribers, self.hub_name)

    @classmethod
    def append_client(cls, client):
        cls.all_connected_clients[client.ID] = client

    @classmethod
    def pop_client(cls, client_id):
        """
        :type client_id: str|int
        """
        return cls.all_connected_clients.pop(client_id, None)



