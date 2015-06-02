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
        with open(os.path.join(path, cls.FILE_NAME), "w") as f:
            classStrings = "".join(cls.__getClassStrings(hubs))
            f.write(cls.WRAPPER.format(main=classStrings))

    @classmethod
    def __getClassStrings(cls, hubs):
        classStrings = []
        for h in hubs:
            classStrings.append(cls.__getHubClassStr(h))
        return classStrings

    WRAPPER = """var $tornado
function $tornadoInit(args){{
    args = args || "";
    $tornado = new WebSocket(args);
    $tornado.__messageID = 0
    $tornado.__returnFunctions = {{}};
    $tornado.__respondTimeout = 3000;
    $tornado.client = {{}};
    $tornado.__constructMessage = function (hubName, functionName, args){{
        args = Array.prototype.slice.call(args);
        id = $tornado.__messageID++
        body = {{"hub":hubName, "function":functionName,"args": args, "ID": id}};
        $tornado.send(JSON.stringify(body));
        return {{done: $tornado.__getReturnFunction(id)}}
    }}
    $tornado.__getReturnFunction = function(ID){{
        return function(onSuccess, onError){{
            f=$tornado.__returnFunctions[ID];
            if($tornado.__returnFunctions[ID] == undefined)
                $tornado.__returnFunctions[ID] = {{}}
            f=$tornado.__returnFunctions[ID]
            f.onSuccess = function(){{onSuccess.apply(onSuccess,arguments);delete $tornado.__returnFunctions[ID]}};
            f.onError = function(){{onError.apply(onError,arguments);delete $tornado.__returnFunctions[ID]}};
            //check __returnFunctions, memory leak
            setTimeout(function(){{
                if($tornado.__returnFunctions[ID] && $tornado.__returnFunctions[ID].onError)
                    $tornado.__returnFunctions[ID].onError("timeOut Error");
            }}, $tornado.__respondTimeout)
        }}
    }}
    $tornado.onmessage = function(ev) {{
        try{{
            msgObj = JSON.parse(ev.data);
            if(msgObj.hasOwnProperty("replay")){{
                f = $tornado.__returnFunctions[msgObj.ID]
                if(msgObj.success && f.onSuccess != undefined)
                    f.onSuccess(msgObj.replay)
                else if(f.onError != undefined)
                    f.onError(msgObj.replay)
            }}else{{
                f = $tornado.client[msgObj.hub][msgObj.function]
                f.apply(f, msgObj.args)
            }}
        }}catch(err){{
            this.onMessageError(err)
        }}
    }}
    $tornado.onMessageError = function(error){{ }}
    $tornado.server = {{}}
    {main}

}}
    """
    CLASS_TEMPLATE = """
    $tornado.server.{name} = {{
        __HUB_NAME : "{name}",
        {functions}
    }}
    $tornado.client.{name} = {{}}"""
    #todo:last part of this function can be extracted
    FUNCTION_TEMPLATE = """
        {name} : function ({args}){{
            {cook}
            return $tornado.__constructMessage(this.__HUB_NAME, "{name}",arguments)
        }}"""
    ARGS_COOK_TEMPLATE = "arguments[{iter}] = {name} || {default};"
