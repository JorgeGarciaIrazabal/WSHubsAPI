import inspect
import os
import jsonpickle
from jsonpickle.pickler import Pickler
from wshubsapi.utils import getDefaults, getArgs, isNewFunction, textTypes
import json

__author__ = 'jgarc'

class JSClientFileGenerator():
    FILE_NAME = "WSHubsApi.js"
    @classmethod
    def __getHubClassStr(cls, class_):
        funcStrings = ",\n".join(cls.__getJSFunctionsStr(class_))
        return cls.CLASS_TEMPLATE.format(name=class_.__HubName__, functions=funcStrings)

    @classmethod
    def __getJSFunctionsStr(cls, class_):
        pickler = Pickler(max_depth=4, max_iter=50, make_refs=False)
        funcStrings = []
        functions = inspect.getmembers(class_.__class__, predicate=isNewFunction)
        for name, method in functions:
            defaults = getDefaults(method)
            for i,default in enumerate(defaults):
                if not isinstance(default, tuple(textTypes)) or not default.startswith("\""):
                    defaults[i] = jsonpickle.encode(pickler.flatten(default))
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

    WRAPPER = """function HubsAPI(url, serverTimeout) {{
    var messageID = 0;
    var returnFunctions = {{}};
    var respondTimeout = (serverTimeout || 5) * 1000;
    var thisApi = this;
    var messagesBeforeOpen = [];
    var onOpenTriggers = [];
    url = url || "";

    this.wsClient = new WebSocket(url);
    this.defaultErrorCallback = null;

    var constructMessage = function (hubName, functionName, args) {{
        args = Array.prototype.slice.call(args);
        var id = messageID++;
        var body = {{"hub": hubName, "function": functionName, "args": args, "ID": id}};
        if(thisApi.wsClient.readyState == 0)
            messagesBeforeOpen.push(JSON.stringify(body));
        else
            thisApi.wsClient.send(JSON.stringify(body));
        return {{done: getReturnFunction(id, {{hubName: hubName, functionName: functionName, args: args}})}}
    }};
    var getReturnFunction = function (ID, callInfo) {{
        return function (onSuccess, onError) {{
            if (returnFunctions[ID] == undefined)
                returnFunctions[ID] = {{}};
            var f = returnFunctions[ID];
            f.onSuccess = function () {{
                if(onSuccess !== undefined)
                    onSuccess.apply(onSuccess, arguments);
                delete returnFunctions[ID]
            }};
            f.onError = function () {{
                if(onError !== undefined)
                    onError.apply(onError, arguments);
                else if (thisApi.defaultErrorCallback != null){{
                    var argumentsArray = [callInfo].concat(arguments);
                    thisApi.defaultErrorCallback.apply(thisApi.defaultErrorCallback.apply, argumentsArray);
                }}
                delete returnFunctions[ID]
            }};
            //check returnFunctions, memory leak
            setTimeout(function () {{
                if (returnFunctions[ID] && returnFunctions[ID].onError)
                    returnFunctions[ID].onError("timeOut Error");
            }}, respondTimeout)
        }}
    }};


    this.wsClient.onopen = function () {{
        onOpenTriggers.forEach(function (trigger) {{
            trigger();
        }});
        messagesBeforeOpen.forEach(function (message) {{
            thisApi.wsClient.send(message);
        }});
    }};

    this.wsClient.addOnOpenTrigger = function(trigger) {{
      if(thisApi.wsClient.readyState == 0)
        onOpenTriggers.push(trigger);
      else if(thisApi.wsClient.readyState == 1)
        trigger();
      else
        throw new Error("web socket is closed");
    }};

    this.wsClient.onmessage = function (ev) {{
        var f,
            msgObj;
        try {{
            msgObj = JSON.parse(ev.data);
            if (msgObj.hasOwnProperty("replay")) {{
                f = returnFunctions[msgObj.ID];
                if (msgObj.success && f != undefined && f.onSuccess != undefined)
                    f.onSuccess(msgObj.replay);
                if (!msgObj.success){{
                    if (f != undefined && f.onError != undefined)
                        f.onError(msgObj.replay);
                }}
            }} else {{
                f = thisApi[msgObj.hub].client[msgObj.function];
                f.apply(f, msgObj.args)
            }}
        }} catch (err) {{
            this.onMessageError(err)
        }}
    }};
    this.wsClient.onMessageError = function (error) {{
    }};
    {main}
}}
    """
    CLASS_TEMPLATE = """
    this.{name} = {{}};
    this.{name}.server = {{
        __HUB_NAME : "{name}",
        {functions}
    }};
    this.{name}.client = {{}};"""

    FUNCTION_TEMPLATE = """
        {name} : function ({args}){{
            {cook}
            return constructMessage(this.__HUB_NAME, "{name}",arguments);
        }}"""

    ARGS_COOK_TEMPLATE = "arguments[{iter}] = {name} == undefined ? {default} : {name};"
