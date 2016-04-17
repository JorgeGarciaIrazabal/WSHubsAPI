WSHubsAPI
================================================

The package makes really easy to establish intuitive communication in a server/clients architecture.<br /><br />
Forget to handle web-socket messages with huge switch cases or maintain url strings for your API-REST.
Just **call server functions from the client** and **call client function from the server** like it is the same program.<br />
But not only that! with this package you will be able to communicate client applications with different languages or communication protocols at the same time!

**Available coding languages:** <br />
* Server side:
   * only python
* Client side:
   * python
   * javascript
   * java/android (on going)
   * c++/arduino (on going)
   * micro-python (planned)

**Communication protocols** <br /> <br />
This package is mainly a message handler so it doesn't matter which communication protocol you use as long as you create a Wrapper to handle it. However, we provide handlers to start coding right away :)
* Web-Sockets for tornado and ws4py
* Http requests for Django and tornado frameworks (of course we lose server to client communication)
* Socket

**Of course, any contribution will be more that appreciated ;)**