import inspect
import os
from WSHubsAPI.utils import getDefaults, getArgs, isNewFunction

__author__ = 'jgarc'

class JSClientFileGenerator():
    FILE_NAME = "WSProtocol.js"
    @classmethod
    def __getHubClassStr(cls, class_):
        funcStrings = ",\n".join(cls.__getJSFunctionsStr(class_))
        return cls.CLASS_TEMPLATE.format(name=class_.__HubName__, functions=funcStrings)

    @classmethod
    def __getJSFunctionsStr(cls, class_):
        funcStrings = []
        functions = inspect.getmembers(class_.__class__, predicate=isNewFunction)
        for name, method in functions:
            defaults = getDefaults(method)
            args = getArgs(method)
            defaultsArray = []
            for i, d in reversed(list(enumerate(defaults))):
                defaultsArray.insert(0,cls.ARGS_COOK_TEMPLATE.format(iter = i, name = args[i], default=d))
            defaultsStr = "\n\t\t\t".join(defaultsArray)
            funcStrings.append(cls.FUNCTION_TEMPLATE.format(name=name, args=", ".join(args), cook=defaultsStr))
        return funcStrings

    @classmethod
    def createFile(cls, path, hubs):
        if not os.path.exists(path): os.makedirs(path)
        with open(os.path.join(path, cls.FILE_NAME), "w") as f:
            classStrings = "".join(cls.__getClassStrings(hubs))
            f.write(cls.WRAPPER.format(main=classStrings))

    @classmethod
    def __getClassStrings(cls, hubs):
        classStrings = []
        for h in hubs:
            classStrings.append(cls.__getHubClassStr(h))
        return classStrings

    WRAPPER = """var $wsConnection
function $wsConnectionInit(args, serverTimeout){{
    args = args || "";
    $wsConnection = new WebSocket(args);
    $wsConnection.__messageID = 0
    $wsConnection.__returnFunctions = {{}};
    $wsConnection.__respondTimeout = serverTimeout || 5000;
    $wsConnection.client = {{}};
    $wsConnection.__constructMessage = function (hubName, functionName, args){{
        args = Array.prototype.slice.call(args);
        id = $wsConnection.__messageID++
        body = {{"hub":hubName, "function":functionName,"args": args, "ID": id}};
        $wsConnection.send(JSON.stringify(body));
        return {{done: $wsConnection.__getReturnFunction(id)}}
    }}
    $wsConnection.__getReturnFunction = function(ID){{
        return function(onSuccess, onError){{
            f=$wsConnection.__returnFunctions[ID];
            if($wsConnection.__returnFunctions[ID] == undefined)
                $wsConnection.__returnFunctions[ID] = {{}}
            f=$wsConnection.__returnFunctions[ID]
            f.onSuccess = function(){{onSuccess.apply(onSuccess,arguments);delete $wsConnection.__returnFunctions[ID]}};
            f.onError = function(){{onError.apply(onError,arguments);delete $wsConnection.__returnFunctions[ID]}};
            //check __returnFunctions, memory leak
            setTimeout(function(){{
                if($wsConnection.__returnFunctions[ID] && $wsConnection.__returnFunctions[ID].onError)
                    $wsConnection.__returnFunctions[ID].onError("timeOut Error");
            }}, $wsConnection.__respondTimeout)
        }}
    }}
    $wsConnection.onmessage = function(ev) {{
        try{{
            msgObj = JSON.parse(ev.data);
            if(msgObj.hasOwnProperty("replay")){{
                f = $wsConnection.__returnFunctions[msgObj.ID]
                if(msgObj.success && f != undefined && f.onSuccess != undefined)
                    f.onSuccess(msgObj.replay)
                else if(f != undefined && f.onError != undefined)
                    f.onError(msgObj.replay)
            }}else{{
                f = $wsConnection.client[msgObj.hub][msgObj.function]
                f.apply(f, msgObj.args)
            }}
        }}catch(err){{
            this.onMessageError(err)
        }}
    }}
    $wsConnection.onMessageError = function(error){{ }}
    $wsConnection.server = {{}}
    {main}

    return $wsConnection;
}}
    """
    CLASS_TEMPLATE = """
    $wsConnection.server.{name} = {{
        __HUB_NAME : "{name}",
        {functions}
    }}
    $wsConnection.client.{name} = {{}}"""
    #todo:last part of this function can be extracted
    FUNCTION_TEMPLATE = """
        {name} : function ({args}){{
            {cook}
            return $wsConnection.__constructMessage(this.__HUB_NAME, "{name}",arguments)
        }}"""
    ARGS_COOK_TEMPLATE = "arguments[{iter}] = {name} == undefined ? {default} : {name};"
