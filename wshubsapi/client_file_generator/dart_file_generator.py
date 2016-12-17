import inflection

from wshubsapi.client_file_generator.client_file_generator import ClientFileGenerator


class DartClientFileGenerator(ClientFileGenerator):
    TAB = "    "

    @classmethod
    def __get_hub_class_str(cls, hub_name, hub_info):
        functions_str = dict(serverFunctions=cls.__get_server_functions_str(hub_info, hub_name),
                             clientFunctions=cls.__get_client_functions_str(hub_info, hub_name),
                             bridgeFunctions=cls.__get_bridge_functions_str(hub_info))
        return cls.CLASS_TEMPLATE.format(name=hub_name, **functions_str)

    @classmethod
    def __get_functions_parameters(cls, methods_info):
        all_parameters = []

        for method_name, method_info in methods_info.items():
            args = [inflection.camelize(arg, False) for arg in method_info["args"]]
            defaults = method_info["defaults"]
            formatted_args = []
            for i, arg in enumerate(reversed(args)):
                if i >= len(defaults):
                    formatted_args.insert(0, arg)
                else:
                    formatted_args.insert(0, arg + " = " + str(defaults[-i - 1]))
                    if i == len(defaults) - 1:
                        formatted_args[0] = "[" + formatted_args[0]
                    if i == len(args) - len(defaults) - 1:
                        formatted_args[0] += "]"

            append_in_args = ("\n" + cls.TAB * 3).join([cls.ARGS_COOK_TEMPLATE.format(name=arg) for arg in args])
            func_parameters = dict(name=method_name,
                                   args=", ".join(formatted_args),
                                   cook=append_in_args,
                                   rawArgs=", ".join(args),
                                   camelCaseName=inflection.camelize(method_name, False))
            all_parameters.append(func_parameters)

        return all_parameters

    @classmethod
    def __get_server_functions_str(cls, hub_info, hub_name):
        all_parameters = cls.__get_functions_parameters(hub_info["serverMethods"])

        def add_map(params):
            params['hubName'] = hub_name
            return params

        all_parameters = map(add_map, all_parameters)
        return "\n".join([cls.SERVER_FUNCTION_TEMPLATE.format(**params) for params in all_parameters])

    @classmethod
    def __get_client_functions_str(cls, hub_info, hub_name):
        all_parameters = cls.__get_functions_parameters(hub_info["clientMethods"])

        def add_map(params):
            params['hubName'] = hub_name
            return params

        all_parameters = map(add_map, all_parameters)
        return "\n".join([cls.CLIENT_FUNCTION_TEMPLATE.format(**params) for params in all_parameters])

    @classmethod
    def __get_bridge_functions_str(cls, hub_info):
        all_parameters = cls.__get_functions_parameters(hub_info["clientMethods"])
        return "\n".join([cls.BRIDGE_FUNCTION_TEMPLATE.format(**params) for params in all_parameters])

    @classmethod
    def __get_attributes_hub_declaration(cls, hubs_info):
        return [cls.ATTRIBUTE_HUB_TEMPLATE_DECLARATION.format(name=name) for name in hubs_info]

    @classmethod
    def __get_attributes_hub_initialization(cls, hubs_info):
        return [cls.ATTRIBUTE_HUB_TEMPLATE_INITIALIZATION.format(name=name) for name in hubs_info]

    @classmethod
    def __get_class_strs(cls, hubs_info):
        class_strings = []
        for hub_name, hub_info in hubs_info.items():
            class_strings.append(cls.__get_hub_class_str(hub_name, hub_info))
        return class_strings

    @classmethod
    def create_file(cls, hubs_info, path):
        parent_dir = cls._construct_api_path(path)
        with open(path, "w") as f:
            class_strings = "".join(cls.__get_class_strs(hubs_info))
            attributes_hubs_declaration = "\n".join(cls.__get_attributes_hub_declaration(hubs_info))
            attributes_hubs_initialization = "\n".join(cls.__get_attributes_hub_initialization(hubs_info))
            f.write(cls.WRAPPER.format(Hubs=class_strings,
                                       attributesHubsDeclaration=attributes_hubs_declaration,
                                       attributesHubsInitialization=attributes_hubs_initialization))

    WRAPPER = '''import 'dart:async';
import 'dart:convert';
import 'dart:html';
import 'dart:mirrors';

class _Serializer {{
    String serialize(obj) {{
        return JSON.encode(_jsonize(obj));
    }}

    _jsonize(var obj) {{
        if (obj is String || obj is num || obj is bool) {{
            return obj;
        }}
        else if (obj is DateTime) {{
            return _jsonize({{"__date_time__": obj
                .toUtc()
                .millisecondsSinceEpoch}});
        }}
        else if (obj is List) {{
            return obj.map((item) {{
                return _jsonize(item);
            }});
        }}
        else if (obj is Map) {{
            obj.forEach((key, item) {{
                obj[key] = _jsonize(item);
            }});
            return obj;
        }}
        else {{
            Map map = new Map();
            InstanceMirror im = reflect(obj);
            ClassMirror cm = im.type;
            var decls = cm.declarations.values.where((dm) => dm is VariableMirror);
            decls.forEach((dm) {{
                var key = MirrorSystem.getName(dm.simpleName);
                var val = im
                    .getField(dm.simpleName)
                    .reflectee;
                map[key] = _jsonize(val);
            }});
            return map;
        }}
    }}

    Map unserialize(objStr) {{
        Map objMap = JSON.decode(objStr);
        return _unjsonize(objMap);
    }}

    _unjsonize(obj) {{
        if (obj is String || obj is num || obj is bool) {{
            return obj;
        }}
        else if (obj is List) {{
            return obj.map((item) {{
                return _unjsonize(item);
            }});
        }}
        else if (obj is Map) {{
            if (obj.containsKey("__date_time__")) {{
                return new DateTime.fromMillisecondsSinceEpoch(obj["__date_time__"], isUtc: true);
            }}
            obj.forEach((key, item) {{
                obj[key] = _unjsonize(item);
            }});
            return obj;
        }}
    }}
}}

String _camelCase(String string) =>
    string
        .toLowerCase()
        .replaceAllMapped(new RegExp(r'[_.\- ]+(\w|$)'), (Match m) {{
        return m[1].toUpperCase();
    }});

class WsHandler {{
    int messageId = 0;
    WebSocket ws;
    bool reconnectScheduled = false;
    bool connected = false;
    Map<int, Completer> futuresHandler = new Map<int, Completer>();
    HubsApi api;

    WsHandler(this.api);

    Future connect(String url, [int retrySeconds = 2]) {{
        var completer = new Completer();
        reconnectScheduled = false;
        ws = new WebSocket(url);
        ws.onOpen.listen((e) {{
            print('Connected');
            connected = true;
            completer.complete('good');
        }});

        ws.onClose.listen((e) {{
            _scheduleReconnect(retrySeconds);
            if (!connected) {{
                connected = false;
                completer.completeError('OnError');
            }}
        }});

        ws.onError.listen((e) {{
            print("Error connecting to ws");
            _scheduleReconnect(retrySeconds);
            if (!connected) {{
                completer.completeError('OnError');
            }}
        }});

        ws.onMessage.listen(onMessage);

        return completer.future;
    }}

    Future sendMessage(String hubName, String functionName, List<Object> args) {{
        var completer = new Completer();
        var id = messageId++;
        var serializedArgs = args.map((arg) {{
            return api.serializer.serialize(arg);
        }}).toList();
        Map body = {{
            'hub': hubName,
            'function': functionName,
            'args': serializedArgs,
            'ID': id
        }};
        futuresHandler[id] = completer;
        ws.send(JSON.encode(body));
        return completer.future;
    }}

    _scheduleReconnect(retrySeconds) {{
        if (!reconnectScheduled) {{
            new Timer(new Duration(seconds: retrySeconds), () =>
                this.connect(retrySeconds = retrySeconds));
        }}
        reconnectScheduled = true;
    }}

    onMessage(MessageEvent e) async {{
        print('message receiver ${{e.data}}');
        Map<String, Object> msgMap = api.serializer.unserialize(e.data);
        if (msgMap.containsKey('reply')) {{
            var completer = futuresHandler[msgMap['ID']];
            msgMap['success']
                ? completer.complete(msgMap['reply'])
                : completer.completeError(msgMap['reply']);
        }} else {{
            msgMap['function'] = _camelCase(msgMap['function']);
            InstanceMirror im = reflect(api);
            var hub = reflect(api)
                .getField(new Symbol(msgMap['hub']))
                .reflectee;
            im = reflect(hub.client);
            Map replyMessage = {{'ID': msgMap['ID']}};
            var reply = null;
            try {{
                reply = await im.invoke(new Symbol(msgMap['function']), msgMap['args']);
                if(reply is Future){{
                    reply = await reply;
                }}
                replyMessage['reply'] = api.serializer.serialize(reply);;
                replyMessage['success'] = true;
            }} catch (exception, stackTrace) {{
                print(stackTrace);
                replyMessage['reply'] = exception.toString();
                replyMessage['success'] = false;
            }} finally {{
                ws.send(JSON.encode(replyMessage));
            }}
        }}
    }}
}}
{Hubs}

class HubsApi {{
    WsHandler wsHandler;
    _Serializer serializer = new _Serializer();
{attributesHubsDeclaration}

    HubsApi() {{
        wsHandler = new WsHandler(this);
{attributesHubsInitialization}
    }}
}}
'''

    CLASS_TEMPLATE = '''
class _{name}Server {{
    WsHandler wsHandler;

    _{name}Server(this.wsHandler);
    {serverFunctions}
}}


class _{name}Client {{
    WsHandler wsHandler;
    {clientFunctions}

    _{name}Client(this.wsHandler);

    _{name}ClientBridge getClients(List clientsIds) {{
        return new _{name}ClientBridge(clientsIds, this.wsHandler);
    }}
}}

class _{name}ClientBridge {{
    List clientsIds;
    WsHandler wsHandler;

    _{name}ClientBridge(this.clientsIds, this.wsHandler);

    {bridgeFunctions}
}}

class _{name} {{
    _{name}Server server;
    _{name}Client client;

    _{name}(WsHandler wsHandler) {{
        server = new _{name}Server(wsHandler);
        client = new _{name}Client(wsHandler);
    }}
}}

'''

    SERVER_FUNCTION_TEMPLATE = '''
        Future {camelCaseName}({args}) {{
            var args = [];
            {cook}
            return this.wsHandler.sendMessage('{hubName}', '{name}', args);
        }}'''

    CLIENT_FUNCTION_TEMPLATE = '''
        Function {camelCaseName};'''

    BRIDGE_FUNCTION_TEMPLATE = '''
    Future {camelCaseName}({args}) {{
        var args = [{rawArgs}];
        var bodyArgs = [clientsIds, 'print_message', args];
        return  this.wsHandler.sendMessage('ChatHub', '_client_to_clients_bridge', bodyArgs);
    }}'''

    ARGS_COOK_TEMPLATE = "args.add({name});"

    ATTRIBUTE_HUB_TEMPLATE_DECLARATION = "    _{name} {name};"
    ATTRIBUTE_HUB_TEMPLATE_INITIALIZATION = "        {name} = new _{name}(wsHandler);"
