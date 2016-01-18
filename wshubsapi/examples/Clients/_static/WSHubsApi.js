/* jshint ignore:start */
/* ignore jslint start */
function HubsAPI(url, serverTimeout) {
    'use strict';

    var messageID = 0,
        returnFunctions = {},
        defaultRespondTimeout = (serverTimeout || 5) * 1000,
        thisApi = this,
        messagesBeforeOpen = [],
        onOpenTriggers = [];
    url = url || '';

    this.clearTriggers = function () {
        messagesBeforeOpen = [];
        onOpenTriggers = [];
    };

    this.connect = function (reconnectTimeout) {
        reconnectTimeout = reconnectTimeout || -1;
        var openPromise = {
            onSuccess : function() {},
            onError : function(error) {}
        };
        function reconnect(error) {
            if (reconnectTimeout !== -1) {
                window.setTimeout(function () {
                    thisApi.connect(reconnectTimeout);
                    thisApi.callbacks.onReconnecting(error);
                }, reconnectTimeout * 1000);
            }
        }

        try {
            this.wsClient = new WebSocket(url);
        } catch (error) {
            reconnect(error);
            return;
        }

        this.wsClient.onopen = function () {
            openPromise.onSuccess();
            openPromise.onError = function () {};
            thisApi.callbacks.onOpen(thisApi);
            onOpenTriggers.forEach(function (trigger) {
                trigger();
            });
            messagesBeforeOpen.forEach(function (message) {
                thisApi.wsClient.send(message);
            });
        };

        this.wsClient.onclose = function (error) {
            openPromise.onError(error);
            thisApi.callbacks.onClose(error);
            reconnect(error);
        };

        this.wsClient.addOnOpenTrigger = function (trigger) {
            if (thisApi.wsClient.readyState === 0) {
                onOpenTriggers.push(trigger);
            } else if (thisApi.wsClient.readyState === 1) {
                trigger();
            } else {
                throw new Error("web socket is closed");
            }
        };

        this.wsClient.onmessage = function (ev) {
            try {
                var f,
                msgObj = JSON.parse(ev.data);
                if (msgObj.hasOwnProperty('replay')) {
                    f = returnFunctions[msgObj.ID];
                    if (msgObj.success && f !== undefined && f.onSuccess !== undefined) {
                        f.onSuccess(msgObj.replay);
                    }
                    if (!msgObj.success) {
                        if (f !== undefined && f.onError !== undefined) {
                            f.onError(msgObj.replay);
                        }
                    }
                } else {
                    f = thisApi[msgObj.hub].client[msgObj.function];
                    f.apply(f, msgObj.args);
                }
            } catch (err) {
                this.onMessageError(err);
            }
        };

        this.wsClient.onMessageError = function (error) {
            thisApi.callbacks.onMessageError(error);
        };

        return { done: function (onSuccess, onError) {
                openPromise.onSuccess = onSuccess;
                openPromise.onError = onError;
            }
        };
    };

    this.callbacks = {
        onClose: function (error) {},
        onOpen: function () {},
        onReconnecting: function () {},
        onMessageError: function (error){}
    };

    this.defaultErrorHandler = null;

    var constructMessage = function (hubName, functionName, args) {
        if(thisApi.wsClient === undefined) {
            throw Error('ws not connected');
        }
        args = Array.prototype.slice.call(args);
        var id = messageID++,
            body = {'hub': hubName, 'function': functionName, 'args': args, 'ID': id};
        if(thisApi.wsClient.readyState === WebSocket.CONNECTING) {
            messagesBeforeOpen.push(JSON.stringify(body));
        } else if (thisApi.wsClient.readyState !== WebSocket.OPEN) {
            window.setTimeout(function () {
                var f = returnFunctions[id];
                if (f !== undefined && f.onError !== undefined) {
                    f.onError('webSocket not connected');
                }
            }, 0);
            return {done: getReturnFunction(id, {hubName: hubName, functionName: functionName, args: args})};
        }
        else {
            thisApi.wsClient.send(JSON.stringify(body));
        }
        return {done: getReturnFunction(id, {hubName: hubName, functionName: functionName, args: args})};
    };
    var getReturnFunction = function (ID, callInfo) {
        return function (onSuccess, onError, respondsTimeout) {
            if (returnFunctions[ID] === undefined) {
                returnFunctions[ID] = {};
            }
            var f = returnFunctions[ID];
            f.onSuccess = function () {
                if(onSuccess !== undefined) {
                    onSuccess.apply(onSuccess, arguments);
                }
                delete returnFunctions[ID];
            };
            f.onError = function () {
                if(onError !== undefined) {
                    onError.apply(onError, arguments);
                } else if (thisApi.defaultErrorHandler !== null){
                    var argumentsArray = [callInfo].concat(arguments);
                    thisApi.defaultErrorHandler.apply(thisApi.defaultErrorHandler.apply, argumentsArray);
                }
                delete returnFunctions[ID];
            };
            //check returnFunctions, memory leak
            respondsTimeout = undefined ? defaultRespondTimeout : respondsTimeout;
            if(respondsTimeout >=0) {
                setTimeout(function () {
                    if (returnFunctions[ID] && returnFunctions[ID].onError) {
                        returnFunctions[ID].onError('timeOut Error');
                    }
                }, defaultRespondTimeout);
            }
        };
    };

    
    this.ChatHub = {};
    this.ChatHub.server = {
        __HUB_NAME : 'ChatHub',
        
        getClientsHolder : function (){
            
            return constructMessage('ChatHub', 'getClientsHolder', arguments);
        },

        classMethod : function (){
            
            return constructMessage('ChatHub', 'classMethod', arguments);
        },

        unsubscribeToHub : function (){
            
            return constructMessage('ChatHub', 'unsubscribeToHub', arguments);
        },

        sendToAll : function (name, message){
            
            return constructMessage('ChatHub', 'sendToAll', arguments);
        },

        getSubscribedClientsToHub : function (){
            
            return constructMessage('ChatHub', 'getSubscribedClientsToHub', arguments);
        },

        static : function (){
            
            return constructMessage('ChatHub', 'static', arguments);
        },

        subscribeToHub : function (){
            
            return constructMessage('ChatHub', 'subscribeToHub', arguments);
        }
    };
    this.ChatHub.client = {};
    this.UtilAPIHub = {};
    this.UtilAPIHub.server = {
        __HUB_NAME : 'UtilAPIHub',
        
        getClientsHolder : function (){
            
            return constructMessage('UtilAPIHub', 'getClientsHolder', arguments);
        },

        unsubscribeToHub : function (){
            
            return constructMessage('UtilAPIHub', 'unsubscribeToHub', arguments);
        },

        getSubscribedClientsToHub : function (){
            
            return constructMessage('UtilAPIHub', 'getSubscribedClientsToHub', arguments);
        },

        getId : function (){
            
            return constructMessage('UtilAPIHub', 'getId', arguments);
        },

        isClientConnected : function (clientId){
            
            return constructMessage('UtilAPIHub', 'isClientConnected', arguments);
        },

        subscribeToHub : function (){
            
            return constructMessage('UtilAPIHub', 'subscribeToHub', arguments);
        },

        setId : function (clientId){
            
            return constructMessage('UtilAPIHub', 'setId', arguments);
        },

        getHubsStructure : function (){
            
            return constructMessage('UtilAPIHub', 'getHubsStructure', arguments);
        }
    };
    this.UtilAPIHub.client = {};
}
/* jshint ignore:end */
/* ignore jslint end */
    