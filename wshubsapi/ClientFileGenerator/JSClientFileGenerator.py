import os

import jsonpickle
from jsonpickle.pickler import Pickler

__author__ = 'jgarc'


class JSClientFileGenerator:
    FILE_NAME = "WSHubsApi.js"

    @classmethod
    def __getClassStrings(cls, hubsInfo):
        classStrings = []
        for hubName, hubInfo in hubsInfo.items():
            classStrings.append(cls.__getHubClassStr(hubName, hubInfo))
        return classStrings

    @classmethod
    def __getHubClassStr(cls, hubName, hubInfo):
        funcStrings = ",\n".join(cls.__getJSFunctionsStr(hubName, hubInfo))
        return cls.CLASS_TEMPLATE.format(name=hubName, functions=funcStrings)

    @classmethod
    def __getJSFunctionsStr(cls, hubName, hubInfo):
        pickler = Pickler(max_depth=4, max_iter=50, make_refs=False)
        funcStrings = []

        for methodName, methodInfo in hubInfo["serverMethods"].items():
            defaults = methodInfo["defaults"]
            for i, default in enumerate(defaults):
                if not isinstance(default, basestring) or not default.startswith("\""):
                    defaults[i] = jsonpickle.encode(pickler.flatten(default))
            args = methodInfo["args"]
            defaultsArray = []
            for i, d in reversed(list(enumerate(defaults))):
                defaultsArray.insert(0, cls.ARGS_COOK_TEMPLATE.format(iter=i, name=args[i], default=d))
            defaultsStr = "\n\t\t\t".join(defaultsArray)
            funcStrings.append(cls.FUNCTION_TEMPLATE.format(name=methodName, args=", ".join(args), cook=defaultsStr,
                                                            hubName=hubName))
        return funcStrings

    @classmethod
    def createFile(cls, path, hubsInfo):
        if not os.path.exists(path): os.makedirs(path)
        with open(os.path.join(path, cls.FILE_NAME), "w") as f:
            classStrings = "".join(cls.__getClassStrings(hubsInfo))
            f.write(cls.WRAPPER.format(main=classStrings))

    WRAPPER = """/* jshint ignore:start */
/* ignore jslint start */
function HubsAPI(url, serverTimeout, wsClientClass) {{
    'use strict';

    var messageID = 0,
        returnFunctions = {{}},
        defaultRespondTimeout = (serverTimeout || 5) * 1000,
        thisApi = this,
        messagesBeforeOpen = [],
        onOpenTriggers = [];
    url = url || '';

    this.clearTriggers = function () {{
        messagesBeforeOpen = [];
        onOpenTriggers = [];
    }};

    this.connect = function (reconnectTimeout) {{
        reconnectTimeout = reconnectTimeout || -1;
        var openPromise = {{
            onSuccess : function() {{}},
            onError : function(error) {{}},
            _connectError: false,
            done: function (onSuccess, onError) {{
                openPromise.onSuccess = onSuccess;
                openPromise.onError = onError;
                if (openPromise._connectError !== false){{
                    openPromise.onError(openPromise._connectError);
                }}
            }}
        }};
        function reconnect(error) {{
            if (reconnectTimeout !== -1) {{
                window.setTimeout(function () {{
                    thisApi.connect(reconnectTimeout);
                    thisApi.callbacks.onReconnecting(error);
                }}, reconnectTimeout * 1000);
            }}
        }}

        try {{
            this.wsClient = wsClientClass === undefined ? new WebSocket(url) : new wsClientClass(url);
        }} catch (error) {{
            reconnect(error);
            openPromise._connectError = error;
            return openPromise;
        }}

        this.wsClient.onopen = function () {{
            openPromise.onSuccess();
            openPromise.onError = function () {{}};
            thisApi.callbacks.onOpen(thisApi);
            onOpenTriggers.forEach(function (trigger) {{
                trigger();
            }});
            messagesBeforeOpen.forEach(function (message) {{
                thisApi.wsClient.send(message);
            }});
        }};

        this.wsClient.onclose = function (error) {{
            openPromise.onError(error);
            thisApi.callbacks.onClose(error);
            reconnect(error);
        }};

        this.wsClient.addOnOpenTrigger = function (trigger) {{
            if (thisApi.wsClient.readyState === 0) {{
                onOpenTriggers.push(trigger);
            }} else if (thisApi.wsClient.readyState === 1) {{
                trigger();
            }} else {{
                throw new Error("web socket is closed");
            }}
        }};

        this.wsClient.onmessage = function (ev) {{
            try {{
                var f,
                msgObj = JSON.parse(ev.data);
                if (msgObj.hasOwnProperty('replay')) {{
                    f = returnFunctions[msgObj.ID];
                    if (msgObj.success && f !== undefined && f.onSuccess !== undefined) {{
                        f.onSuccess(msgObj.replay);
                    }}
                    if (!msgObj.success) {{
                        if (f !== undefined && f.onError !== undefined) {{
                            f.onError(msgObj.replay);
                        }}
                    }}
                }} else {{
                    f = thisApi[msgObj.hub].client[msgObj.function];
                    if (f!== undefined) {{
                        var replayMessage = {{ID: msgObj.ID}}
                        try {{
                            replayMessage.replay =  f.apply(f, msgObj.args);
                            replayMessage.success = true;
                        }} catch(e){{
                            replayMessage.success = false;
                            replayMessage.replay = e.toString();
                        }} finally {{
                            replayMessage.replay = replayMessage.replay === undefined ? null: replayMessage.replay;
                            thisApi.wsClient.send(JSON.stringify(replayMessage))
                        }}
                    }} else {{
                        this.onClientFunctionNotFound(msgObj.hub, msgObj.function);
                    }}
                }}
            }} catch (err) {{
                this.onMessageError(err);
            }}
        }};

        this.wsClient.onMessageError = function (error) {{
            thisApi.callbacks.onMessageError(error);
        }};

        return openPromise;
    }};

    this.callbacks = {{
        onClose: function (error) {{}},
        onOpen: function () {{}},
        onReconnecting: function () {{}},
        onMessageError: function (error){{}},
        onClientFunctionNotFound: function (hub, func) {{}}
    }};

    this.defaultErrorHandler = null;

    var constructMessage = function (hubName, functionName, args) {{
        if(thisApi.wsClient === undefined) {{
            throw Error('ws not connected');
        }}
        args = Array.prototype.slice.call(args);
        var id = messageID++,
            body = {{'hub': hubName, 'function': functionName, 'args': args, 'ID': id}};
        if(thisApi.wsClient.readyState === WebSocket.CONNECTING) {{
            messagesBeforeOpen.push(JSON.stringify(body));
        }} else if (thisApi.wsClient.readyState !== WebSocket.OPEN) {{
            window.setTimeout(function () {{
                var f = returnFunctions[id];
                if (f !== undefined && f.onError !== undefined) {{
                    f.onError('webSocket not connected');
                }}
            }}, 0);
            return {{done: getReturnFunction(id, {{hubName: hubName, functionName: functionName, args: args}})}};
        }}
        else {{
            thisApi.wsClient.send(JSON.stringify(body));
        }}
        return getReturnFunction(id, {{hubName: hubName, functionName: functionName, args: args}});
    }};

    var getReturnFunction = function (ID, callInfo) {{

        function Future (ID, callInfo) {{
            var self = this;
            this.done = function(onSuccess, onError, respondsTimeout) {{
                if (returnFunctions[ID] === undefined) {{
                    returnFunctions[ID] = {{}};
                }}
                var f = returnFunctions[ID];
                f.onSuccess = function () {{
                    try{{
                        if(onSuccess !== undefined) {{
                            onSuccess.apply(onSuccess, arguments);
                         }}
                    }} finally {{
                        delete returnFunctions[ID];
                        self._finally();
                    }}
                }};
                f.onError = function () {{
                    try{{
                        if(onError !== undefined) {{
                            onError.apply(onError, arguments);
                        }} else if (thisApi.defaultErrorHandler !== null){{
                            var argumentsArray = [callInfo].concat(arguments);
                            thisApi.defaultErrorHandler.apply(thisApi.defaultErrorHandler, argumentsArray);
                        }}
                    }} finally {{
                        delete returnFunctions[ID];
                        self._finally();
                    }}
                }};
                //check returnFunctions, memory leak
                respondsTimeout = undefined ? defaultRespondTimeout : respondsTimeout;
                if(respondsTimeout >=0) {{
                    setTimeout(function () {{
                        if (returnFunctions[ID] && returnFunctions[ID].onError) {{
                            returnFunctions[ID].onError('timeOut Error');
                        }}
                    }}, defaultRespondTimeout);
                }}
                return self;
            }};
            this.finally = function (finallyCallback) {{
                self._finally = finallyCallback;
            }};
            this._finally = function () {{}};
        }};
        return new Future(ID, callInfo)
    }};

    {main}
}}
/* jshint ignore:end */
/* ignore jslint end */
    """
    CLASS_TEMPLATE = """
    this.{name} = {{}};
    this.{name}.server = {{
        __HUB_NAME : '{name}',
        {functions}
    }};
    this.{name}.client = {{}};"""

    FUNCTION_TEMPLATE = """
        {name} : function ({args}){{
            {cook}
            return constructMessage('{hubName}', '{name}', arguments);
        }}"""

    ARGS_COOK_TEMPLATE = "arguments[{iter}] = {name} === undefined ? {default} : {name};"
