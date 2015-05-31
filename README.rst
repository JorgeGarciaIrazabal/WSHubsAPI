WSHubsAPI
================================================

The ``WSHubsAPI`` package/module alows an intuitive communication between back-end (Python) and front-end (Python, JS, JAVA or Android) applications throw the webSocket protocol.

Examples of usage
-----------------
Below is an example of how easy is to create a chat room with this API.

Server side
~~~~~~~~~~~~~~~~~~~~~
In this example we will use the tornado framework and the tornado clientHandler for the ws connections.

	>>> 
	from tornado import web, ioloop
	from HubDecorator import HubDecorator
	from ConnectionHandlers.Tornado import ClientHandler
	class IndexHandler(web.RequestHandler):
		def get(self):
			self.render("index.html")
	 app = web.Application([(r'/', IndexHandler),(r'/ws/(.*)', ClientHandler)], static_path = "")
  >>> 
  if __name__ == '__main__
		@HubDecorator.hub
		class ChatHub:
			def sendToAll(self, message):
				conn = HubDecorator.getConnection()
				conn.otherClients.onChatMessage(conn, message)
				return len(conn.allClients) #returns the number of clients connected to the hub
		HubDecorator.constructJSFile("")#should be in the static_path to be read by Tornado framework
		app.listen(8888)
    ioloop.IOLoop.instance().start()
    
Client side JS client
~~~~~~~~~~~~~~~
works like:

>>> 
<!DOCTYPE html>
<html>
<head>
    <title>tornado WebSocket example</title>
    <!--This file will be automatically created from server-->
    <script type="text/javascript" src="WSProtocol.js"></script>
</head>
<body>
 <span id="message">"Waiting connection</span>
    <script>
    $tornadoInit('ws://localhost:8888/')
    $tornado.client.ChatHub.onChatMessage = function(message){ alert(message) }
    $tornado.onopen = function(){
        document.getElementById("message").innerHTML = "Connected"
    };
    $tornado.onclose = function(ev){
        document.getElementById("message").innerHTML = "Closed"
    };
    $tornado.onerror = function(ev){
      alert(ev)
    };
</script>
</body>
</html>

Enabling logging
~~~~~~~~~~~~~~~~

If you're wondering how prefixing the above command with ``sudo`` would
end up being helpful, here's how it works:

>>> import logging
>>> logging.basicConfig()
>>> logging.getLogger().setLevel(logging.DEBUG)

Contact
-------

The latest version of ``WSHubsAPI`` is available on PyPI_ and GitHub_. 
For bug reports please create an
issue on GitHub_. If you have questions, suggestions, etc. feel free to send me
an e-mail at `jorge.girazabal@gmail.com`_.

License
-------

This software is licensed under the `MIT license`_.

© 2015 Jorge Garcia Irazabal.