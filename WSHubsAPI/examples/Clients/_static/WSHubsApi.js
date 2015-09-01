function HubsAPI(url, serverTimeout) {
    var messageID = 0;
    var returnFunctions = {};
    var respondTimeout = (serverTimeout || 5) * 1000;
    var thisApi = this;
    var messagesBeforeOpen = [];
    var onOpenTriggers = [];
    url = url || "";

    this.wsClient = new WebSocket(url);
    this.defaultErrorCallback = null;

    var constructMessage = function (hubName, functionName, args) {
        args = Array.prototype.slice.call(args);
        var id = messageID++;
        var body = {"hub": hubName, "function": functionName, "args": args, "ID": id};
        if(thisApi.wsClient.readyState == 0)
            messagesBeforeOpen.push(JSON.stringify(body));
        else
            thisApi.wsClient.send(JSON.stringify(body));
        return {done: getReturnFunction(id, {hubName: hubName, functionName: functionName, args: args})}
    };
    var getReturnFunction = function (ID, callInfo) {
        return function (onSuccess, onError) {
            if (returnFunctions[ID] == undefined)
                returnFunctions[ID] = {};
            var f = returnFunctions[ID];
            f.onSuccess = function () {
                if(onSuccess !== undefined)
                    onSuccess.apply(onSuccess, arguments);
                delete returnFunctions[ID]
            };
            f.onError = function () {
                if(onError !== undefined)
                    onError.apply(onError, arguments);
                else if (thisApi.defaultErrorCallback != null){
                    var argumentsArray = [callInfo].concat(arguments);
                    thisApi.defaultErrorCallback.apply(thisApi.defaultErrorCallback.apply, argumentsArray);
                }
                delete returnFunctions[ID]
            };
            //check returnFunctions, memory leak
            setTimeout(function () {
                if (returnFunctions[ID] && returnFunctions[ID].onError)
                    returnFunctions[ID].onError("timeOut Error");
            }, respondTimeout)
        }
    };


    this.wsClient.onopen = function () {
        onOpenTriggers.forEach(function (trigger) {
            trigger();
        });
        messagesBeforeOpen.forEach(function (message) {
            thisApi.wsClient.send(message);
        });
    };

    this.wsClient.addOnOpenTrigger = function(trigger) {
      if(thisApi.wsClient.readyState == 0)
        onOpenTriggers.push(trigger);
      else if(thisApi.wsClient.readyState == 1)
        trigger();
      else
        throw new Error("web socket is closed");
    };

    this.wsClient.onmessage = function (ev) {
        var f,
            msgObj;
        try {
            msgObj = JSON.parse(ev.data);
            if (msgObj.hasOwnProperty("replay")) {
                f = returnFunctions[msgObj.ID];
                if (msgObj.success && f != undefined && f.onSuccess != undefined)
                    f.onSuccess(msgObj.replay);
                if (!msgObj.success){
                    if (f != undefined && f.onError != undefined)
                        f.onError(msgObj.replay);
                }
            } else {
                f = thisApi[msgObj.hub].client[msgObj.function];
                f.apply(f, msgObj.args)
            }
        } catch (err) {
            this.onMessageError(err)
        }
    };
    this.wsClient.onMessageError = function (error) {
    };
    
    this.ChatHub = {};
    this.ChatHub.server = {
        __HUB_NAME : "ChatHub",
        
        getNumOfClientsConnected : function (){
            
            return constructMessage(this.__HUB_NAME, "getNumOfClientsConnected",arguments);
        },

        sendToAll : function (name, message){
            
            return constructMessage(this.__HUB_NAME, "sendToAll",arguments);
        }
    };
    this.ChatHub.client = {};
}
    