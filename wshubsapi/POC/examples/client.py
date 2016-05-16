# file created by the server
from client_api.hubs_api import HubsAPI


def message_published(user_name, msg):
    print("{} posted:\n{}".format(user_name, msg))


if __name__ == '__main__':
    ws = HubsAPI('ws://127.0.0.1:8888/')
    ws.connect()
    name = raw_input("What is your name: ")
    # defining client function to be called from server
    ws.ForumHub.client.messagePublished = message_published

    print("Hello %s!" % name)
    while True:
        message = raw_input("Write whatever you want to post it in the forum: \n")
        # ws.ForumHub.server.publish_message is automaticly by the server in HugsAPI module
        server_replay = ws.ForumHub.server.publish_message(name, message).result(timeout=3)
        print("Server reply: {}".format(server_replay))
