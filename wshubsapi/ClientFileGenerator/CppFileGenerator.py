import inspect
import logging
import os
from os import listdir
from os.path import isfile

from wshubsapi.utils import isFunctionForWSClient, getArgs, ASCII_UpperCase, getModulePath

__author__ = 'jgarc'
log = logging.getLogger(__name__)


class CppFileGenerator:
    FILE_NAME = "HubsApi.hpp"

    @staticmethod
    def __getHubObjectName(hubName):
        return hubName[0].lower() + hubName[1:]

    @classmethod
    def __getHubClassStr(cls, hubName, methodsInfo):
        HUB_NAME = hubName

        methods = []
        for methodName, arguments in methodsInfo["serverMethods"].items():
            methods.append(cls.__getFunctionString(methodName, **arguments))
        METHODS = "\n\t\t\t".join(methods)
        HUB_OBJECT_DECLARATION = "{0} {1}".format(hubName, cls.__getHubObjectName(hubName))
        return cls.HUB_TEMPLATE.format(**locals())

    @classmethod
    def __getFunctionString(cls, methodName, args, defaults):
        types = ["TYPE_" + l for l in ASCII_UpperCase[:len(args)]]
        METHOD_NAME = methodName
        if len(args) == 0:
            TEMPLATE_TYPES = ""
        else:
            TEMPLATE_TYPES = "\n\t\t\ttemplate<{}>".format(", ".join(["class " + t for t in types]))
        fArgs = [types[i] + " " + arg for i, arg in enumerate(args)]
        if len(defaults)>0:
            fArgs = fArgs[:-len(defaults)] + [f + " = " + defaults[i] for i, f in enumerate(fArgs[-len(defaults):])]
        FUNCTION_ARGS = ", ".join(fArgs)
        MESSAGE_ARGS = "\n\t\t\t\t".join([cls.ARGS_COOK_TEMPLATE.format(arg=arg) for arg in args])
        return cls.METHOD_TEMPLATE.format(**locals())

    @classmethod
    def createFile(cls, path, hubsInfo):
        clientFolder = os.path.abspath(os.path.join(path, cls.FILE_NAME))
        if not os.path.exists(path):
            os.makedirs(path)
        hubs = []
        CONSTRUCTOR = cls.__getConstructor(hubsInfo)
        for hubName, methods in hubsInfo.items():
            hubs.append(cls.__getHubClassStr(hubName, methods))
        HUBS = "\n\t".join(hubs)

        with open(clientFolder, "w") as f:
            f.write(cls.MAIN.format(**locals()))

    @classmethod
    def __getConstructor(cls, hubsInfo):
        constructors = []
        initializations = []
        for hubName in hubsInfo:
            hubObjName = cls.__getHubObjectName(hubName)
            constructors.append("{}()".format(hubObjName))
            initializations.append("{}.server.hubsAPI = this;".format(hubObjName))
        HUBS_CONSTRUCTORS = ", ".join(constructors)
        HUBS_INITIALIZATION = "\n\t\t".join(initializations)
        return cls.CONSTRUCTOR.format(**locals())

    @classmethod
    def __getAttributesHubs(cls, hubs):
        return "\n".join([cls.ATTRIBUTE_HUB_TEMPLATE.format(name=hub.__HubName__) for hub in hubs])

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
            if (messageObj.containsKey("replay")) {{
                JsonArray &args = jsonBuffer.createArray();
                args.add(messageObj["replay"]);
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

