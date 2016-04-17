from wshubsapi.hubs_inspector import HubsInspector
from wshubsapi.connection_handlers.tornado_handler import ConnectionHandler
from tornado import web, ioloop
from wshubsapi.hub import Hub
import logging

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    class ForumHub(Hub):
        def publish_message(self, user_name, message):
            # get all connected clients to call client functions directly from here
            all_clients = self.clients.get_all_clients()
            # messagePosted function has to be defined in the client side
            all_clients.messagePublished(user_name, message)
            return "Sent to %d user(s)" % len(all_clients)

    # inspect Hubs in project to be included in the api environment
    HubsInspector.inspect_implemented_hubs()
    # create api modules to be used by the clients
    HubsInspector.construct_python_file("client_api")  # python api module will be created in "_static" folder
    HubsInspector.construct_js_file("client_api")  # javascript api library will be created in "_static" folder

    # initialize server
    app = web.Application([(r'/(.*)', ConnectionHandler)])
    app.listen(8888)
    logging.debug("server is listening in port: {}".format(8888))
    ioloop.IOLoop.instance().start()
