

try:
	from Queue import Queue
except:
	from queue import Queue

import datetime
import inspect
import os
import string
import sys
from inspect import getargspec
from concurrent.futures import ThreadPoolExecutor

DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'

try:
	textTypes = [str, unicode]
except:
	textTypes = [str]
ASCII_UpperCase = string.uppercase if sys.version_info[0] == 2 else string.ascii_uppercase


def getArgs(method):
	args = getargspec(method).args
	if args is None: return []
	for arg in ("self", "cls", "_sender"):
		try:
			args.remove(arg)
		except:
			pass
	return args


def getDefaults(method):
	d = getargspec(method).defaults
	if d is None: return []
	d = list(d)
	for i in range(len(d)):
		if isinstance(d[i], tuple(textTypes)):  # todo: check with python 3
			d[i] = '"%s"' % d[i]
	return d


def isNewFunction(method):
	from WSHubsAPI.Hub import Hub
	isFunction = lambda x: inspect.ismethod(x) or inspect.isfunction(x)
	functions = inspect.getmembers(Hub, predicate=isFunction)
	functionNames = [f[0] for f in functions]

	return isFunction(method) and not method.__name__.startswith("_") and method.__name__ not in functionNames


def getModulePath():
	frame = inspect.currentframe().f_back
	info = inspect.getframeinfo(frame)
	file = info.filename
	return os.path.dirname(os.path.abspath(file))


class WSMessagesReceivedQueue(Queue):
	MAX_WORKERS = 15

	def __init__(self):
		Queue.__init__(self)
		self.executor = ThreadPoolExecutor(max_workers=self.MAX_WORKERS)

	def startThreads(self):
		for i in range(self.MAX_WORKERS):
			self.executor.submit(self.onMessage)

	def onMessage(self):
		while True:
			try:
				msg, connection = self.get()
				connection.onMessage(msg)
			except Exception as e:
				print(str(e))# todo: create a call back for this exception

from jsonpickle import handlers


def setSerializerDateTimeHandler():
	class WSDateTimeObjects(handlers.BaseHandler):
		def flatten(self, obj, data):
			return obj.strftime(DATE_TIME_FORMAT)

	handlers.register(datetime.datetime, WSDateTimeObjects)
	handlers.register(datetime.date, WSDateTimeObjects)
	handlers.register(datetime.time, WSDateTimeObjects)
