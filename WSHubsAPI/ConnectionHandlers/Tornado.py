import logging
from WSHubsAPI.CommProtocol import CommProtocol
import tornado.websocket

__author__ = 'Jorge'
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class ConnectionHandler(tornado.websocket.WebSocketHandler):

	def data_received(self, chunk):
		pass

	commProtocol = CommProtocol()

	def __init__(self, application, request, **kwargs):
		super(ConnectionHandler, self).__init__(application, request, **kwargs)
		self._commHandler = self.commProtocol.constructCommHandler(self)
		self._commHandler.writeMessage = self.writeMessage
		self.ID = None

	def writeMessage(self, message):
		log.debug("message to %s:\n%s" % (self._commHandler.ID, message))
		self.write_message(message)

	def open(self, *args):
		try:
			id = int(args[0])
		except:
			id = None
		self.ID = self._commHandler.onOpen(id)
		log.debug("open new connection with ID: {} ".format(self.ID))

	def on_message(self, message):
		log.debug("Message received from ID: {}\n{} ".format(self.ID, message))
		self._commHandler.onAsyncMessage(message)

	def on_close(self):
		log.debug("client closed %s" % self._commHandler.__dict__.get("ID", "None"))
		self._commHandler.onClose()

	def check_origin(self, origin):
		return True
