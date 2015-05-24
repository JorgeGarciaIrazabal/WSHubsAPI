__author__ = 'jgarc'

class HubDecoratorConfig:
    class Template():
        def __init__(self):
            self.class_ = None
            self.function = None
            self.argsCook = None

    JS_WRAPPER = """var $tornado
function $tornadoInit(args){{
    args = args || "";
    $tornado = new WebSocket('ws://localhost:8888/ws/'+args);
    $tornado.__messageID = 0
    $tornado.__returnFunctions = {{}};
    $tornado.__respondTimeout = 3000
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

    JS_CLASS_TEMPLATE = """
    $tornado.server.{name} = {{
        __HUB_NAME : "{name}",
        {functions}
    }}
    $tornado.client.{name} = {{}}"""
    JS_FUNCTION_TEMPLATE = """
        {name} : function ({args}){{
            {cook}
            id = $tornado.__messageID++
            body = {{"hub":this.__HUB_NAME, "function":"{name}","args":[], "ID": id}};
            for(var i =0; i<arguments.length;i++)
                body.args.push(arguments[i])
            $tornado.send(JSON.stringify(body));
            return {{done: $tornado.__getReturnFunction(id)}}
        }}"""
    JS_ARGS_COOK_TEMPLATE = "arguments[{iter}] = {name} || {default};"


    JAVA_CLASS_TEMPLATE = """
    public static class {name} {{
        public static final String HUB_NAME = "{name}";
        {functions}
    }}"""
    JAVA_FUNCTION_TEMPLATE = """
        public static {types} FunctionResult {name} ({args}) throws JSONException{{
            int messageId= connection.getNewMessageId();
            JSONObject msgObj = new JSONObject();
            JSONArray argsArray = new JSONArray();
            {cook}
            msgObj.put("hub",HUB_NAME);
            msgObj.put("function","{name}");
            msgObj.put("args", argsArray);
            msgObj.put("ID", messageId);
            connection.send(msgObj.toString());
            return new FunctionResult(connection,messageId);
        }}"""
    JAVA_ARGS_COOK_TEMPLATE = "TornadoServer.addArg(argsArray,{arg});"

    JAVA_WRAPPER = """package %s;
import com.google.gson.Gson;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import java.net.URISyntaxException;

public class TornadoServer {{
    private static Gson gson = new Gson();
    private static TornadoConnection connection;

    public static void init(String uriStr) throws URISyntaxException {{
        connection = new TornadoConnection(uriStr);
        connection.connect();
    }}
    private static <TYPE_ARG> void addArg(JSONArray argsArray, TYPE_ARG arg) throws JSONException {{
        try {{
            argsArray.put(arg);
        }} catch (Exception e) {{
            argsArray.put(new JSONObject(gson.toJson(arg)));
        }}
    }}
    {main}
}}
    """

    @staticmethod
    def getJSTemplates():
        templates = HubDecoratorConfig.Template()
        templates.class_ = HubDecoratorConfig.JS_CLASS_TEMPLATE
        templates.function = HubDecoratorConfig.JS_FUNCTION_TEMPLATE
        templates.argsCook = HubDecoratorConfig.JS_ARGS_COOK_TEMPLATE
        return templates

    @staticmethod
    def getJAVATemplates():
        templates = HubDecoratorConfig.Template()
        templates.class_ = HubDecoratorConfig.JAVA_CLASS_TEMPLATE
        templates.function = HubDecoratorConfig.JAVA_FUNCTION_TEMPLATE
        templates.argsCook = HubDecoratorConfig.JAVA_ARGS_COOK_TEMPLATE
        return templates

    def __init__(self):
        pass

