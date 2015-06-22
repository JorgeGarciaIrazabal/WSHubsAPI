import org.json.JSONObject;
import java.lang.reflect.Method;
import java.util.HashMap;

public abstract class WSHubsEventHandler implements WebSocketEventHandler {
    public HashMap<Integer, FunctionResult.Handler> returnFunctions = new HashMap<>();
    public String clientHubPrefix = this.getClass().getPackage() + "." + "ClientHubs.Client_";

    @Override
    public void onMessage(WebSocketMessage message) {
        try {
            JSONObject msgObj = new JSONObject(message.getText());
            if (msgObj.has("replay")) {//critical point TODO:use mutex or conditions to prevent concurrent problems
                if (returnFunctions.containsKey(msgObj.getInt("ID"))) {
                    FunctionResult.Handler task = returnFunctions.get(msgObj.getInt("ID"));
                    if (!task.isDone()) {
                        if (msgObj.getBoolean("success"))
                            task._onSuccess(msgObj.get("replay"));
                        else
                            task._onError(msgObj.get("replay"));
                    }
                }
            } else {
                Class<?> c = Class.forName(clientHubPrefix + msgObj.getString("hub"));
                Method[] methods = c.getDeclaredMethods();
                String functionName = msgObj.getString("function").toUpperCase();
                for (Method m : methods) {
                    if (m.getName().toUpperCase().equals(functionName)) {
                        int parametersLenght = m.getParameterTypes().length;
                        Object[] args = new Object[parametersLenght];
                        for (int i = 0; i < parametersLenght; i++)
                            args[i] = msgObj.getJSONArray("args").get(i);
                        m.invoke(null, args);
                        return;
                    }
                }
            }
        } catch (Exception e) {
            System.out.println("ERROR - " + e.toString());
            //Log.e(TAG, "Error " + e.getMessage());
        }
    }

    @Override
    public void onPing() {

    }

    @Override
    public void onPong() {

    }

}
