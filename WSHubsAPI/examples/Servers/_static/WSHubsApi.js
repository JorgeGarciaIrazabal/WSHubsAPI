function HubsAPI(url, serverTimeout) {
    var messageID = 0;
    var returnFunctions = {};
    var respondTimeout = (serverTimeout || 5) * 1000;
    var thisApi = this;
    url = url || "";

    this.wsClient = new WebSocket(url);

    var constructMessage = function (hubName, functionName, args) {
        args = Array.prototype.slice.call(args);
        var id = messageID++;
        var body = {"hub": hubName, "function": functionName, "args": args, "ID": id};
        thisApi.wsClient.send(JSON.stringify(body));
        return {done: getReturnFunction(id)}
    };
    var getReturnFunction = function (ID) {
        return function (onSuccess, onError) {
            if (returnFunctions[ID] == undefined)
                returnFunctions[ID] = {};
            var f = returnFunctions[ID];
            f.onSuccess = function () {
                onSuccess.apply(onSuccess, arguments);
                delete returnFunctions[ID]
            };
            f.onError = function () {
                onError.apply(onError, arguments);
                delete returnFunctions[ID]
            };
            //check returnFunctions, memory leak
            setTimeout(function () {
                if (returnFunctions[ID] && returnFunctions[ID].onError)
                    returnFunctions[ID].onError("timeOut Error");
            }, respondTimeout)
        }
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
                else if (f != undefined && f.onError != undefined)
                    f.onError(msgObj.replay)
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
        
        sendToAll : function (name, message){
            
            return constructMessage(this.__HUB_NAME, "sendToAll",arguments);
        }
    }
    this.ChatHub.client = {}
}
    