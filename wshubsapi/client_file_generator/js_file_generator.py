import os

import inflection
import jsonpickle
from jsonpickle.pickler import Pickler

__author__ = 'jgarc'


class JSClientFileGenerator:
    FILE_NAME = "hubsApi.js"

    def __init__(self):
        raise Exception("static class, do not create an instance of it")

    @classmethod
    def __get_class_strs(cls, hubs_info):
        class_strings = []
        for hub_name, hub_info in hubs_info.items():
            class_strings.append(cls.__get_hub_class_str(hub_name, hub_info))
        return class_strings

    @classmethod
    def __get_hub_class_str(cls, hub_name, hub_info):
        func_strings = ",\n".join(cls.__get_js_functions_str(hub_name, hub_info))
        return cls.CLASS_TEMPLATE.format(name=hub_name, functions=func_strings)

    @classmethod
    def __get_js_functions_str(cls, hub_name, hub_info):
        pickler = Pickler(max_depth=4, max_iter=50, make_refs=False)
        func_strings = []

        for method_name, method_info in hub_info["serverMethods"].items():
            defaults = method_info["defaults"]
            for i, default in enumerate(defaults):
                if not isinstance(default, basestring) or not default.startswith("\""):
                    defaults[i] = jsonpickle.encode(pickler.flatten(default))
            args = [inflection.camelize(arg, False) for arg in method_info["args"]]
            defaults_array = []
            for i, d in reversed(list(enumerate(defaults))):
                defaults_array.insert(0, cls.ARGS_COOK_TEMPLATE.format(iter=i, name=args[i], default=d))
            defaults_str = "\n\t\t\t".join(defaults_array)
            func_strings.append(cls.FUNCTION_TEMPLATE.format(name=method_name, args=", ".join(args),
                                                             cook=defaults_str, hubName=hub_name,
                                                             camelCaseName=inflection.camelize(method_name, False)))
        return func_strings

    @classmethod
    def create_file(cls, path, hubs_info):
        if not os.path.exists(path):
            os.makedirs(path)
        with open(os.path.join(path, cls.FILE_NAME), "w") as f:
            class_strings = "".join(cls.__get_class_strs(hubs_info))
            f.write(cls.WRAPPER.format(main=class_strings))

    WRAPPER = """/* jshint ignore:start */
/* ignore jslint start */
function HubsAPI(url, serverTimeout, wsClientClass, PromiseClass) {{
    'use strict';

    PromiseClass = PromiseClass || Promise;
    if (!PromiseClass.prototype.finally) {{
        PromiseClass.prototype.finally = function (callback) {{
            var p = this.constructor;
            return this.then(
                function (value) {{
                    return p.resolve(callback()).then(function () {{
                        return value;
                    }});
                }},
                function (reason) {{
                    return p.resolve(callback()).then(function () {{
                        throw reason;
                    }});
                }});
        }};
    }}

    if (!PromiseClass.prototype.setTimeout) {{
        PromiseClass.prototype.setTimeout = function (timeout) {{
            clearTimeout(this._timeoutID);
            setTimeout(timeoutError(this._reject), timeout);
            return this;
        }};
    }}

    function timeoutError(reject) {{
        return function () {{
            reject(new Error('timeout error'));
        }};
    }}

    var messageID = 0,
        promisesHandler = {{}},
        defaultRespondTimeout = serverTimeout || 5000,
        thisApi = this,
        messagesBeforeOpen = [],
        emptyFunction = function () {{}},
        onOpenTriggers = [];
    url = url || '';

    function toCamelCase(str) {{
        return str.replace(/_([a-z])/g, function (g) {{ return g[1].toUpperCase(); }});
    }}

    this.clearTriggers = function () {{
        messagesBeforeOpen = [];
        onOpenTriggers = [];
    }};

    this.connect = function (reconnectTimeout) {{
        return new PromiseClass(function (resolve, reject) {{
            reconnectTimeout = reconnectTimeout || -1;
            function reconnect(error) {{
                if (reconnectTimeout !== -1) {{
                    window.setTimeout(function () {{
                        thisApi.connect(reconnectTimeout);
                        thisApi.callbacks.onReconnecting(error);
                    }}, reconnectTimeout * 1000);
                }}
            }}

            try {{
                thisApi.wsClient = wsClientClass === undefined ? new WebSocket(url) : new wsClientClass(url);
            }} catch (error) {{
                reconnect(error);
                reject(error);
            }}

            thisApi.wsClient.onopen = function () {{
                resolve();
                thisApi.callbacks.onOpen(thisApi);
                onOpenTriggers.forEach(function (trigger) {{
                    trigger();
                }});
                messagesBeforeOpen.forEach(function (message) {{
                    thisApi.wsClient.send(message);
                }});
            }};

            thisApi.wsClient.onclose = function (error) {{
                reject(error);
                thisApi.callbacks.onClose(error);
                reconnect(error);
            }};

            thisApi.wsClient.addOnOpenTrigger = function (trigger) {{
                if (thisApi.wsClient.readyState === 0) {{
                    onOpenTriggers.push(trigger);
                }} else if (thisApi.wsClient.readyState === 1) {{
                    trigger();
                }} else {{
                    throw new Error('web socket is closed');
                }}
            }};

            thisApi.wsClient.onmessage = function (ev) {{
                try {{
                    var promiseHandler,
                        msgObj = JSON.parse(ev.data);
                    if (msgObj.hasOwnProperty('replay')) {{
                        promiseHandler = promisesHandler[msgObj.ID];
                        msgObj.success ? promiseHandler.resolve(msgObj.replay) : promiseHandler.reject(msgObj.replay);
                    }} else {{
                        msgObj.function = toCamelCase(msgObj.function);
                        var executor = thisApi[msgObj.hub].client[msgObj.function];
                        if (executor !== undefined) {{
                            var replayMessage = {{ID: msgObj.ID}};
                            try {{
                                replayMessage.replay = executor.apply(executor, msgObj.args);
                                replayMessage.success = true;
                            }} catch (e) {{
                                replayMessage.success = false;
                                replayMessage.replay = e.toString();
                            }} finally {{
                                replayMessage.replay = replayMessage.replay === undefined ? null : replayMessage.replay;
                                thisApi.wsClient.send(JSON.stringify(replayMessage));
                            }}
                        }} else {{
                            thisApi.onClientFunctionNotFound(msgObj.hub, msgObj.function);
                        }}
                    }}
                }} catch (err) {{
                    thisApi.wsClient.onMessageError(err);
                }}
            }};

            thisApi.wsClient.onMessageError = function (error) {{
                thisApi.callbacks.onMessageError(error);
            }};
        }});
    }};

    this.callbacks = {{
        onClose: emptyFunction,
        onOpen: emptyFunction,
        onReconnecting: emptyFunction,
        onMessageError: emptyFunction,
        onClientFunctionNotFound: emptyFunction
    }};

    this.defaultErrorHandler = null;

    var constructMessage = function (hubName, functionName, args) {{
        if (thisApi.wsClient === undefined) {{
            throw new Error('ws not connected');
        }}
        var promise,
            timeoutID = null,
            _reject;
        promise = new PromiseClass(function (resolve, reject) {{
            args = Array.prototype.slice.call(args);
            var id = messageID++,
                body = {{'hub': hubName, 'function': functionName, 'args': args, 'ID': id}};
            promisesHandler[id] = {{}};
            promisesHandler[id].resolve = resolve;
            promisesHandler[id].reject = reject;
            timeoutID = setTimeout(timeoutError(reject), defaultRespondTimeout);
            _reject = reject;

            if (thisApi.wsClient.readyState === WebSocket.CONNECTING) {{
                messagesBeforeOpen.push(JSON.stringify(body));
            }} else if (thisApi.wsClient.readyState !== WebSocket.OPEN) {{
                reject('webSocket not connected');
            }} else {{
                thisApi.wsClient.send(JSON.stringify(body));
            }}
        }});
        promise._timeoutID = timeoutID;
        promise._reject = _reject;
        return promise;
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
        {camelCaseName} : function ({args}){{
            {cook}
            return constructMessage('{hubName}', '{name}', arguments);
        }}"""

    ARGS_COOK_TEMPLATE = "arguments[{iter}] = {name} === undefined ? {default} : {name};"
