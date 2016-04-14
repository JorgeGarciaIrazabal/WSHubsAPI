import inspect
import logging
import os
from os import listdir
from os.path import isfile

from wshubsapi.utils import is_function_for_ws_client, get_args, ASCII_UpperCase, get_module_path

__author__ = 'jgarc'
log = logging.getLogger(__name__)


class JAVAFileGenerator:
    SERVER_FILE_NAME = "WSHubsApi.java"
    CLIENT_PACKAGE_NAME = "ClientHubs"
    EXTRA_FILES_FOLDER = "JavaExtraFiles"
    CLIENT_HUB_PREFIX = "Client_"

    def __init__(self):
        raise Exception("static class, do not create an instance of it")

    @classmethod
    def __get_hub_class_str(cls, class_):
        func_str = "\n".join(cls.__get_js_functions_str(class_))
        return cls.CLASS_TEMPLATE.format(name=class_.__HubName__, functions=func_str, prefix=cls.CLIENT_HUB_PREFIX)

    @classmethod
    def __get_js_functions_str(cls, class_):
        func_str = []
        functions = inspect.getmembers(class_, predicate=is_function_for_ws_client)
        for name, method in functions:
            args = get_args(method)
            types = ["TYPE_" + l for l in ASCII_UpperCase[:len(args)]]
            args_types = [types[i] + " " + arg for i, arg in enumerate(args)]
            types = "<" + ", ".join(types) + ">" if len(types) > 0 else ""
            to_json = "\n\t\t\t\t".join([cls.ARGS_COOK_TEMPLATE.format(arg=a) for a in args])
            args_types = ", ".join(args_types)
            func_str.append(cls.FUNCTION_TEMPLATE.format(name=name, args=args_types, types=types, cook=to_json))
        return func_str

    @classmethod
    def create_file(cls, path, package, hubs):
        if not os.path.exists(path):
            os.makedirs(path)
        attributes_hubs = cls.__get_attributes_hubs(hubs)
        with open(os.path.join(path, cls.SERVER_FILE_NAME), "w") as f:
            class_str = "".join(cls.__get_class_strings(hubs))
            f.write(cls.WRAPPER.format(main=class_str,
                                       package=package,
                                       clientPackage=cls.CLIENT_PACKAGE_NAME,
                                       attributesHubs=attributes_hubs))
        cls.__copy_extra_files(path, package)

    @classmethod
    def create_client_template(cls, path, package, hubs):  # todo: dynamically get client function names
        client_folder = os.path.join(path, cls.CLIENT_PACKAGE_NAME)
        if not os.path.exists(client_folder):
            os.makedirs(client_folder)
        for hub in hubs:
            client_hub_file = os.path.join(client_folder, cls.CLIENT_HUB_PREFIX + hub.__HubName__) + '.java'
            if not os.path.exists(client_hub_file):
                with open(client_hub_file, "w") as f:
                    class_str = cls.CLIENT_CLASS_TEMPLATE.format(package=package,
                                                                 name=hub.__HubName__,
                                                                 prefix=cls.CLIENT_HUB_PREFIX)
                    f.write(class_str)

    @classmethod
    def __get_class_strings(cls, hubs):
        class_str = []
        for h in hubs:
            class_str.append(cls.__get_hub_class_str(h))
        return class_str

    @classmethod
    def __get_attributes_hubs(cls, hubs):
        return "\n".join([cls.ATTRIBUTE_HUB_TEMPLATE.format(name=hub.__HubName__) for hub in hubs])

    @classmethod
    def __copy_extra_files(cls, dst_path, package):
        files_path = os.path.join(get_module_path(), cls.EXTRA_FILES_FOLDER)
        files = [f for f in listdir(files_path) if isfile(os.path.join(files_path, f)) and f.endswith(".java")]
        for f in files:
            if not isfile(os.path.join(dst_path, f)):
                abs_dst_path = os.path.join(dst_path, f)
                abs_ori_path = os.path.join(files_path, f)
                cls.__copy_file(abs_dst_path, abs_ori_path, package)
                log.info("Created file: %s", abs_dst_path)

    @classmethod
    def __copy_file(cls, abs_dst_path, abs_ori_path, package):
        with open(abs_ori_path) as oriFile:
            with open(abs_dst_path, 'w') as dstFile:
                ori_str = oriFile.read()
                dst_str = "package %s;\n" % package + ori_str
                dstFile.write(dst_str)

    CLASS_TEMPLATE = """
    public class {name} {{
        public class Server {{
            public static final String HUB_NAME = "{name}";
            {functions}
        }}
        public Server server = new Server();
        public {prefix}{name} client = new {prefix}{name}(WSHubsApi.this);
    }}"""
    FUNCTION_TEMPLATE = """
            public {types} FunctionResult {name} ({args}) throws JSONException{{
                JSONArray argsArray = new JSONArray();
                {cook}
                return __constructMessage(HUB_NAME, "{name}",argsArray);
            }}"""
    ARGS_COOK_TEMPLATE = "__addArg(argsArray,{arg});"

    WRAPPER = """package {package};
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import org.json.simple.JSONArray;
import org.json.JSONException;
import org.json.simple.JSONObject;
import java.net.URISyntaxException;
import java.lang.reflect.Modifier;
import {package}.{clientPackage}.*;
public class %s {{//TODO: do not use static functions, we might want different connections
    private static Gson gson = new GsonBuilder()
            .excludeFieldsWithModifiers(Modifier.FINAL, Modifier.TRANSIENT, Modifier.STATIC)
            .serializeNulls()
            .setDateFormat("yyyy/MM/dd HH:mm:ss S")
            .create();
    public WSHubsAPIClient wsClient;
{attributesHubs}

    public %s (String uriStr, WSHubsEventHandler wsHubsEventHandler) throws URISyntaxException {{
        wsClient = new WSHubsAPIClient(uriStr);
        wsHubsEventHandler.setWsHubsApi(this);
        wsClient.setEventHandler(wsHubsEventHandler);
    }}

    public boolean isConnected(){{return wsClient.isConnected();}}

    private FunctionResult __constructMessage (String hubName, String functionName, JSONArray argsArray) throws JSONException{{
        int messageId= wsClient.getNewMessageId();
        JSONObject msgObj = new JSONObject();
        msgObj.put("hub",hubName);
        msgObj.put("function",functionName);
        msgObj.put("args", argsArray);
        msgObj.put("ID", messageId);
        wsClient.send(msgObj.toJSONString());
        return new FunctionResult(wsClient,messageId);
    }}

    private static <TYPE_ARG> void __addArg(JSONArray argsArray, TYPE_ARG arg) throws JSONException {{
        try {{
            if(arg.getClass().isPrimitive())
                argsArray.add(arg);
            else
                argsArray.add(gson.toJsonTree(arg));
        }} catch (Exception e) {{ //todo: do something with this exception
            JSONArray aux = new JSONArray();
            aux.add(gson.toJsonTree(arg));
            argsArray.add(aux);
        }}
    }}
    {main}
}}
    """ % (SERVER_FILE_NAME[:-5], SERVER_FILE_NAME[:-5])

    CLIENT_CLASS_TEMPLATE = """package {package}.%s;
import {package}.ClientBase;
import {package}.WSHubsApi;
public class {prefix}{name} extends ClientBase {{
    public {prefix}{name}(WSHubsApi wsHubsApi) {{
        super(wsHubsApi);
    }}
    // Todo: create client side functions
}}""" % CLIENT_PACKAGE_NAME
    ATTRIBUTE_HUB_TEMPLATE = "    public {name} {name} = new {name}();"
