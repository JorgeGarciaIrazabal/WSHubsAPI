'use strict';
/* jshint ignore:start */
/* ignore jslint start */
function HubsAPI(serverTimeout, wsClientClass, PromiseClass) {

    var messageID = 0,
        promisesHandler = {},
        defaultRespondTimeout = serverTimeout || 5000,
        thisApi = this,
        messagesBeforeOpen = [],
        emptyFunction = function () {return function () {}}, //redefine any empty function as required
        onOpenTriggers = [];

    PromiseClass = PromiseClass || Promise;
    if (!PromiseClass.prototype.finally) {
        PromiseClass.prototype.finally = function (callback) {
            var p = this.constructor;
            return this.then(
                function (value) {
                    return p.resolve(callback()).then(function () {
                        return value;
                    });
                },
                function (reason) {
                    return p.resolve(callback()).then(function () {
                        throw reason;
                    });
                });
        };
    }

    if (!PromiseClass.prototype.setTimeout) {
        PromiseClass.prototype.setTimeout = function (timeout) {
            clearTimeout(this._timeoutID);
            setTimeout(timeoutError(this._reject), timeout);
            return this;
        };
    }

    function timeoutError(reject) {
        return function () {
            reject(new Error('timeout error'));
        };
    }

    function toCamelCase(str) {
        return str.replace(/_([a-z])/g, function (g) { return g[1].toUpperCase(); });
    }

    this.clearTriggers = function () {
        messagesBeforeOpen = [];
        onOpenTriggers = [];
    };

    this.connect = function (url, reconnectTimeout) {
        return new PromiseClass(function (resolve, reject) {
            reconnectTimeout = reconnectTimeout || -1;
            function reconnect(error) {
                if (reconnectTimeout !== -1) {
                    window.setTimeout(function () {
                        thisApi.connect(url, reconnectTimeout);
                        thisApi.onReconnecting(error);
                    }, reconnectTimeout);
                }
            }

            try {
                thisApi.wsClient = wsClientClass === undefined ? new WebSocket(url) : new wsClientClass(url);
            } catch (error) {
                reconnect(error);
                return reject(error);
            }

            thisApi.wsClient.onopen = function () {
                resolve();
                thisApi.onOpen(thisApi);
                onOpenTriggers.forEach(function (trigger) {
                    trigger();
                });
                messagesBeforeOpen.forEach(function (message) {
                    thisApi.wsClient.send(message);
                });
            };

            thisApi.wsClient.onclose = function (error) {
                reject(error);
                thisApi.onClose(error);
                reconnect(error);
            };

            thisApi.wsClient.addOnOpenTrigger = function (trigger) {
                if (thisApi.wsClient.readyState === 0) {
                    onOpenTriggers.push(trigger);
                } else if (thisApi.wsClient.readyState === 1) {
                    trigger();
                } else {
                    throw new Error('web socket is closed');
                }
            };

            thisApi.wsClient.onmessage = function (ev) {
                try {
                    var promiseHandler,
                        msgObj = JSON.parse(ev.data);
                    if (msgObj.hasOwnProperty('reply')) {
                        promiseHandler = promisesHandler[msgObj.ID];
                        msgObj.success ? promiseHandler.resolve(msgObj.reply) : promiseHandler.reject(msgObj.reply);
                    } else {
                        msgObj.function = toCamelCase(msgObj.function);
                        var executor = thisApi[msgObj.hub].client[msgObj.function];
                        if (executor !== undefined) {
                            var replayMessage = {ID: msgObj.ID};
                            try {
                                replayMessage.reply = executor.apply(executor, msgObj.args);
                                replayMessage.success = true;
                            } catch (e) {
                                replayMessage.success = false;
                                replayMessage.reply = e.toString();
                            } finally {
                                if (replayMessage.reply instanceof PromiseClass) {
                                    replayMessage.reply.then(function (result) {
                                        replayMessage.success = true;
                                        replayMessage.reply = result;
                                        thisApi.wsClient.send(JSON.stringify(replayMessage));
                                    }, function (error) {
                                        replayMessage.success = false;
                                        replayMessage.reply = error;
                                        thisApi.wsClient.send(JSON.stringify(replayMessage));
                                    });
                                } else {
                                    replayMessage.reply = replayMessage.reply === undefined ? null : replayMessage.reply;
                                    thisApi.wsClient.send(JSON.stringify(replayMessage));
                                }
                            }
                        } else {
                            thisApi.onClientFunctionNotFound(msgObj.hub, msgObj.function, msgObj.args);
                        }
                    }
                } catch (err) {
                    thisApi.wsClient.onMessageError(err);
                }
            };

            thisApi.wsClient.onMessageError = function (error) {
                thisApi.onMessageError(error);
            };
        });
    };

    this.onClose = emptyFunction();
    this.onOpen = emptyFunction();
    this.onReconnecting = emptyFunction();
    this.onMessageError = emptyFunction();
    this.onClientFunctionNotFound = emptyFunction();

    this.defaultErrorHandler = null;

    var constructMessage = function (hubName, functionName, args) {
        if (thisApi.wsClient === undefined) {
            throw new Error('ws not connected');
        }
        var promise,
            timeoutID = null,
            _reject;
        promise = new PromiseClass(function (resolve, reject) {
            args = Array.prototype.slice.call(args);
            var id = messageID++,
                body = {'hub': hubName, 'function': functionName, 'args': args, 'ID': id};
            promisesHandler[id] = {};
            promisesHandler[id].resolve = resolve;
            promisesHandler[id].reject = reject;
            timeoutID = setTimeout(timeoutError(reject), defaultRespondTimeout);
            _reject = reject;

            if (thisApi.wsClient.readyState === WebSocket.CONNECTING) {
                messagesBeforeOpen.push(JSON.stringify(body));
            } else if (thisApi.wsClient.readyState !== WebSocket.OPEN) {
                reject('webSocket not connected');
            } else {
                thisApi.wsClient.send(JSON.stringify(body));
            }
        });
        promise._timeoutID = timeoutID;
        promise._reject = _reject;
        return promise;
    };
    
    this.SubHub = {};
    this.SubHub.server = {
        __HUB_NAME : 'SubHub',
        
        subscribeToHub : function (){
            
            return constructMessage('SubHub', 'subscribe_to_hub', arguments);
        },

        unsubscribeFromHub : function (){
            
            return constructMessage('SubHub', 'unsubscribe_from_hub', arguments);
        },

        getSubscribedClientsIds : function (){
            
            return constructMessage('SubHub', 'get_subscribed_clients_ids', arguments);
        }
    };
    this.SubHub.client = {
        __HUB_NAME : 'SubHub',
        
    };
    this.SubHub.getClients = function(clientsIds){
        return {
            clientsIds: clientsIds,
            call: function (functionName, functionArgs) {
                var bodyArgs = [this.clientsIds, functionName, functionArgs];
                return constructMessage('SubHub', '_client_to_clients_bridge', bodyArgs);
            },
        }
    };
    this.UtilsAPIHub = {};
    this.UtilsAPIHub.server = {
        __HUB_NAME : 'UtilsAPIHub',
        
        unsubscribeFromHub : function (){
            
            return constructMessage('UtilsAPIHub', 'unsubscribe_from_hub', arguments);
        },

        subscribeToHub : function (){
            
            return constructMessage('UtilsAPIHub', 'subscribe_to_hub', arguments);
        },

        getHubsStructure : function (){
            
            return constructMessage('UtilsAPIHub', 'get_hubs_structure', arguments);
        },

        getId : function (){
            
            return constructMessage('UtilsAPIHub', 'get_id', arguments);
        },

        getSubscribedClientsIds : function (){
            
            return constructMessage('UtilsAPIHub', 'get_subscribed_clients_ids', arguments);
        },

        setId : function (clientId){
            
            return constructMessage('UtilsAPIHub', 'set_id', arguments);
        },

        isClientConnected : function (clientId){
            
            return constructMessage('UtilsAPIHub', 'is_client_connected', arguments);
        }
    };
    this.UtilsAPIHub.client = {
        __HUB_NAME : 'UtilsAPIHub',
        
    };
    this.UtilsAPIHub.getClients = function(clientsIds){
        return {
            clientsIds: clientsIds,
            call: function (functionName, functionArgs) {
                var bodyArgs = [this.clientsIds, functionName, functionArgs];
                return constructMessage('UtilsAPIHub', '_client_to_clients_bridge', bodyArgs);
            },
        }
    };
    this.SubHub3 = {};
    this.SubHub3.server = {
        __HUB_NAME : 'SubHub3',
        
        subscribeToHub : function (){
            
            return constructMessage('SubHub3', 'subscribe_to_hub', arguments);
        },

        unsubscribeFromHub : function (){
            
            return constructMessage('SubHub3', 'unsubscribe_from_hub', arguments);
        },

        getSubscribedClientsIds : function (){
            
            return constructMessage('SubHub3', 'get_subscribed_clients_ids', arguments);
        }
    };
    this.SubHub3.client = {
        __HUB_NAME : 'SubHub3',
        
    };
    this.SubHub3.getClients = function(clientsIds){
        return {
            clientsIds: clientsIds,
            call: function (functionName, functionArgs) {
                var bodyArgs = [this.clientsIds, functionName, functionArgs];
                return constructMessage('SubHub3', '_client_to_clients_bridge', bodyArgs);
            },
        }
    };
    this.ChatHub = {};
    this.ChatHub.server = {
        __HUB_NAME : 'ChatHub',
        
        unsubscribeFromHub : function (){
            
            return constructMessage('ChatHub', 'unsubscribe_from_hub', arguments);
        },

        subscribeToHub : function (){
            
            return constructMessage('ChatHub', 'subscribe_to_hub', arguments);
        },

        sendToAll : function (name, message){
            arguments[1] = message === undefined ? "hello" : message;
            return constructMessage('ChatHub', 'send_to_all', arguments);
        },

        getSubscribedClientsIds : function (){
            
            return constructMessage('ChatHub', 'get_subscribed_clients_ids', arguments);
        },

        sendMessageToClient : function (message, clientId){
            
            return constructMessage('ChatHub', 'send_message_to_client', arguments);
        },

        raiseException : function (exceptionMessage){
            
            return constructMessage('ChatHub', 'raise_exception', arguments);
        }
    };
    this.ChatHub.client = {
        __HUB_NAME : 'ChatHub',
        
    };
    this.ChatHub.getClients = function(clientsIds){
        return {
            clientsIds: clientsIds,
            call: function (functionName, functionArgs) {
                var bodyArgs = [this.clientsIds, functionName, functionArgs];
                return constructMessage('ChatHub', '_client_to_clients_bridge', bodyArgs);
            },
        }
    };
    this.SubHub1 = {};
    this.SubHub1.server = {
        __HUB_NAME : 'SubHub1',
        
        subscribeToHub : function (){
            
            return constructMessage('SubHub1', 'subscribe_to_hub', arguments);
        },

        unsubscribeFromHub : function (){
            
            return constructMessage('SubHub1', 'unsubscribe_from_hub', arguments);
        },

        getSubscribedClientsIds : function (){
            
            return constructMessage('SubHub1', 'get_subscribed_clients_ids', arguments);
        }
    };
    this.SubHub1.client = {
        __HUB_NAME : 'SubHub1',
        
    };
    this.SubHub1.getClients = function(clientsIds){
        return {
            clientsIds: clientsIds,
            call: function (functionName, functionArgs) {
                var bodyArgs = [this.clientsIds, functionName, functionArgs];
                return constructMessage('SubHub1', '_client_to_clients_bridge', bodyArgs);
            },
        }
    };
    this.EchoHub = {};
    this.EchoHub.server = {
        __HUB_NAME : 'EchoHub',
        
        subscribeToHub : function (){
            
            return constructMessage('EchoHub', 'subscribe_to_hub', arguments);
        },

        unsubscribeFromHub : function (){
            
            return constructMessage('EchoHub', 'unsubscribe_from_hub', arguments);
        },

        getSubscribedClientsIds : function (){
            
            return constructMessage('EchoHub', 'get_subscribed_clients_ids', arguments);
        },

        echo : function (message){
            
            return constructMessage('EchoHub', 'echo', arguments);
        },

        echoToSender : function (message){
            
            return constructMessage('EchoHub', 'echo_to_sender', arguments);
        }
    };
    this.EchoHub.client = {
        __HUB_NAME : 'EchoHub',
        
    };
    this.EchoHub.getClients = function(clientsIds){
        return {
            clientsIds: clientsIds,
            call: function (functionName, functionArgs) {
                var bodyArgs = [this.clientsIds, functionName, functionArgs];
                return constructMessage('EchoHub', '_client_to_clients_bridge', bodyArgs);
            },
        }
    };
    this.SubHub2 = {};
    this.SubHub2.server = {
        __HUB_NAME : 'SubHub2',
        
        subscribeToHub : function (){
            
            return constructMessage('SubHub2', 'subscribe_to_hub', arguments);
        },

        unsubscribeFromHub : function (){
            
            return constructMessage('SubHub2', 'unsubscribe_from_hub', arguments);
        },

        getSubscribedClientsIds : function (){
            
            return constructMessage('SubHub2', 'get_subscribed_clients_ids', arguments);
        }
    };
    this.SubHub2.client = {
        __HUB_NAME : 'SubHub2',
        
    };
    this.SubHub2.getClients = function(clientsIds){
        return {
            clientsIds: clientsIds,
            call: function (functionName, functionArgs) {
                var bodyArgs = [this.clientsIds, functionName, functionArgs];
                return constructMessage('SubHub2', '_client_to_clients_bridge', bodyArgs);
            },
        }
    };
}
/* jshint ignore:end */
/* ignore jslint end */
    