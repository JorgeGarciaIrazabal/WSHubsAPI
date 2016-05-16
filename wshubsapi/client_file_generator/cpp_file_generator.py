import logging
import os

from wshubsapi.utils import ASCII_UpperCase

__author__ = 'JorgeGarciaIrazabal'
log = logging.getLogger(__name__)


class CppFileGenerator:
    def __init__(self):
        raise Exception("static class, do not create an instance of it")

    FILE_NAME = "HubsApi.hpp"

    @staticmethod
    def __get_hub_object_name(hub_name):
        return hub_name[0].lower() + hub_name[1:]

    @classmethod
    def __get_hub_class_str(cls, hub_name, methods_info):
        HUB_NAME = hub_name

        methods = []
        for method_name, arguments in methods_info["serverMethods"].items():
            methods.append(cls.__get_function_string(method_name, **arguments))
        METHODS = "\n\t\t\t".join(methods)
        HUB_OBJECT_DECLARATION = "{0} {1}".format(hub_name, cls.__get_hub_object_name(hub_name))
        return cls.HUB_TEMPLATE.format(**locals())

    @classmethod
    def __get_function_string(cls, method_name, args, defaults):
        types = ["TYPE_" + l for l in ASCII_UpperCase[:len(args)]]
        METHOD_NAME = method_name
        if len(args) == 0:
            TEMPLATE_TYPES = ""
        else:
            TEMPLATE_TYPES = "\n\t\t\ttemplate<{}>".format(", ".join(["class " + t for t in types]))
        f_args = [types[i] + " " + arg for i, arg in enumerate(args)]
        if len(defaults) > 0:
            f_args = f_args[:-len(defaults)] + [f + " = " + defaults[i] for i, f in enumerate(f_args[-len(defaults):])]
        FUNCTION_ARGS = ", ".join(f_args)
        MESSAGE_ARGS = "\n\t\t\t\t".join([cls.ARGS_COOK_TEMPLATE.format(arg=arg) for arg in args])
        return cls.METHOD_TEMPLATE.format(**locals())

    @classmethod
    def create_file(cls, path, hubs_info):
        client_folder = os.path.abspath(os.path.join(path, cls.FILE_NAME))
        if not os.path.exists(path):
            os.makedirs(path)
        hubs = []
        CONSTRUCTOR = cls.__get_constructor(hubs_info)
        for hub_name, methods in hubs_info.items():
            hubs.append(cls.__get_hub_class_str(hub_name, methods))
        HUBS = "\n\t".join(hubs)

        with open(client_folder, "w") as f:
            f.write(cls.MAIN.format(**locals()))

    @classmethod
    def __get_constructor(cls, hubs_info):
        constructors = []
        initializations = []
        for hub_name in hubs_info:
            hub_obj_name = cls.__get_hub_object_name(hub_name)
            constructors.append("{}()".format(hub_obj_name))
            initializations.append("{}.server.hubsAPI = this;".format(hub_obj_name))
        HUBS_CONSTRUCTORS = ", ".join(constructors)
        HUBS_INITIALIZATION = "\n\t\t".join(initializations)
        return cls.CONSTRUCTOR.format(**locals())

    CONSTRUCTOR = """
    HubsAPI() : {HUBS_CONSTRUCTORS}{{
        {HUBS_INITIALIZATION}
    }}"""

    HUB_TEMPLATE = """class {HUB_NAME} {{
    public:
        class Server {{
        public:
            HubsAPI *hubsAPI;
            void writeMessage(string message) {{
                hubsAPI->writeMessage(message);
            }}
            {METHODS}
        }};

        Server server;
    }};

    {HUB_OBJECT_DECLARATION};
    """

    METHOD_TEMPLATE = """{TEMPLATE_TYPES}
            promise {METHOD_NAME} ({FUNCTION_ARGS}){{
                JsonObject &body = jsonBuffer.createObject();
                body["hub"] = "UtilsAPIHub";
                body["function"] = "{METHOD_NAME}";
                body["ID"] = __globalID++;
                JsonArray &args = body.createNestedArray("args");
                {MESSAGE_ARGS}
                string jsonStr = "";
                body.printTo(jsonStr);
                writeMessage(jsonStr);
                return promise(body.get("ID"));
            }}"""
    ARGS_COOK_TEMPLATE = "args.add({arg});"

    MAIN = """
#ifndef HUBAPI_H
#define HUBAPI_H

#define API_SEP "*API_SEP*"
#define API_SEP_LEN 9
DynamicJsonBuffer jsonBuffer;
using namespace std;

int __globalID = 1;
const int HASH_SIZE = 10;
string __messageBuffer = "";

class FunctionHolder {{
public:
    void (*success)(JsonArray &);
    void (*error)(JsonArray &);
}};

FunctionHolder FunctionHolderBuffer[HASH_SIZE];

void emptyFunction(JsonArray &j) {{
}}

class promise {{
public:
    int ID;

    promise(int ID) {{
        this->ID = ID;
    }}
    void done(void (*success)(JsonArray &), void (*error)(JsonArray &) = emptyFunction) {{
        FunctionHolder fh;
        fh.success = success;
        fh.error = error;
        FunctionHolderBuffer[ID % HASH_SIZE] = fh;
    }}
}};

class HubsAPI {{
public:
    virtual void connect() = 0;

    void disconnect() {{ }};

    virtual void writeMessage(string message) = 0;

    void static receiveMessage(string message) {{
        while (message.find(API_SEP) != -1) {{
            int sepPos = message.find(API_SEP);
            __messageBuffer += message.substr(0, sepPos);
            message = message.substr(sepPos + API_SEP_LEN);
            JsonObject &messageObj = jsonBuffer.parseObject(__messageBuffer);
            int ID = messageObj.get("ID");
            if (messageObj.containsKey("reply")) {{
                JsonArray &args = jsonBuffer.createArray();
                args.add(messageObj["reply"]);
                FunctionHolderBuffer[ID % HASH_SIZE].success(args);
            }} else if (messageObj.containsKey("args")) {{
                JsonArray &args = messageObj.createNestedArray("args");
                FunctionHolderBuffer[ID % HASH_SIZE].success(args);
            }}
            __messageBuffer = "";
        }}
        __messageBuffer = message;
    }};

    {HUBS}
    {CONSTRUCTOR}
}};
#endif //HUBAPI_H"""
