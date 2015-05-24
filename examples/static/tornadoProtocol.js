var $tornado
function $tornadoInit(args){
    args = args || "";
    $tornado = new WebSocket('ws://localhost:8888/ws/'+args);
    $tornado.__messageID = 0
    $tornado.__returnFunctions = {};
    $tornado.__respondTimeout = 3000;
    $tornado.client = {};
    $tornado.__getReturnFunction = function(ID){
        return function(onSuccess, onError){
            f=$tornado.__returnFunctions[ID];
            if($tornado.__returnFunctions[ID] == undefined)
                $tornado.__returnFunctions[ID] = {}
            f=$tornado.__returnFunctions[ID]
            f.onSuccess = function(){onSuccess.apply(onSuccess,arguments);delete $tornado.__returnFunctions[ID]};
            f.onError = function(){onError.apply(onError,arguments);delete $tornado.__returnFunctions[ID]};
            //check __returnFunctions, memory leak
            setTimeout(function(){
                if($tornado.__returnFunctions[ID] && $tornado.__returnFunctions[ID].onError)
                    $tornado.__returnFunctions[ID].onError("timeOut Error");
            }, $tornado.__respondTimeout)
        }
    }
    $tornado.onmessage = function(ev) {
        try{
            msgObj = JSON.parse(ev.data);
            if(msgObj.hasOwnProperty("replay")){
                f = $tornado.__returnFunctions[msgObj.ID]
                if(msgObj.success && f.onSuccess != undefined)
                    f.onSuccess(msgObj.replay)
                else if(f.onError != undefined)
                    f.onError(msgObj.replay)
            }else{
                f = $tornado.client[msgObj.hub][msgObj.function]
                f.apply(f, msgObj.args)
            }
        }catch(err){
            this.onMessageError(err)
        }
    }
    $tornado.onMessageError = function(error){ }
    $tornado.server = {}
    
    $tornado.server.TestClass2 = {
        __HUB_NAME : "TestClass2",
        
        tast : function (a, b, c){
            arguments[0] = a || 5;
			arguments[1] = b || 1;
			arguments[2] = c || 3;
            id = $tornado.__messageID++
            body = {"hub":this.__HUB_NAME, "function":"tast","args":[], "ID": id};
            for(var i =0; i<arguments.length;i++)
                body.args.push(arguments[i])
            $tornado.send(JSON.stringify(body));
            return {done: $tornado.__getReturnFunction(id)}
        },

        test : function (a, b){
            arguments[0] = a || 1;
			arguments[1] = b || 2;
            id = $tornado.__messageID++
            body = {"hub":this.__HUB_NAME, "function":"test","args":[], "ID": id};
            for(var i =0; i<arguments.length;i++)
                body.args.push(arguments[i])
            $tornado.send(JSON.stringify(body));
            return {done: $tornado.__getReturnFunction(id)}
        }
    }
    $tornado.client.TestClass2 = {}
    $tornado.server.TestClass = {
        __HUB_NAME : "TestClass",
        
        tast : function (a, b, c){
            arguments[0] = a || 5;
			arguments[1] = b || 1;
			arguments[2] = c || 3;
            id = $tornado.__messageID++
            body = {"hub":this.__HUB_NAME, "function":"tast","args":[], "ID": id};
            for(var i =0; i<arguments.length;i++)
                body.args.push(arguments[i])
            $tornado.send(JSON.stringify(body));
            return {done: $tornado.__getReturnFunction(id)}
        },

        test : function (a, b){
            arguments[0] = a || 1;
			arguments[1] = b || 2;
            id = $tornado.__messageID++
            body = {"hub":this.__HUB_NAME, "function":"test","args":[], "ID": id};
            for(var i =0; i<arguments.length;i++)
                body.args.push(arguments[i])
            $tornado.send(JSON.stringify(body));
            return {done: $tornado.__getReturnFunction(id)}
        }
    }
    $tornado.client.TestClass = {}

}
    