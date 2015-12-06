import json
import logging
import logging.config
import sys
import time

logging.config.dictConfig(json.load(open('logging.json')))
if sys.version_info[0] == 2:
	input = raw_input

# file created by the server
from _static.WSHubsApi import HubsAPI


def printMessage(senderName, message):
	print(u"From {0}: {1}".format(senderName, message))


def singleAction(index):
	ws = HubsAPI('ws://127.0.0.1:8888/')
	ws.connect()

	ws.ChatHub.client.onMessage = printMessage
	name = "jorge {}".format(index)
	for i in range(3):
		time.sleep(0.03)
		message = "message {}".format(i)
		ws.ChatHub.server.sendToAll(name, message).done(
			lambda m: sys.stdout.write("message sent to %d client(s)\n" % m),
			lambda m: sys.stdout.write(str(m)))


if __name__ == '__main__':
	connections = []
	for i in range(5):
		connections.append(HubsAPI('ws://127.0.0.1:8888/'))
		connections[-1].connect()
		connections[-1].ChatHub.client.onMessage = printMessage

	print("waiting...")
	print("starting")
	for j in range(1):
		for i, conn in enumerate(connections):
			if i % 10 == 0:
				print("going for {}".format(i))
			conn.ChatHub.server.sendToAll(str(i), "message {}".format(i)).done(
				lambda m: m + m,
				lambda m: sys.stdout.write(str(m)))

	print("end")
	time.sleep(100)
