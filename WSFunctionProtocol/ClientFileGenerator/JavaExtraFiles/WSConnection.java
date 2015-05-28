package tornado;

import org.json.JSONObject;

import java.io.IOException;
import java.lang.reflect.Method;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicInteger;

import javax.naming.CommunicationException;

public class WSConnection extends WebSocket {
    public static final String TAG = "Websocket";
    private HashMap<Integer, FunctionResult.Handler> returnFunctions = new HashMap<>();
    private AtomicInteger messageId = new AtomicInteger();
    public int getNewMessageId (){
    	return messageId.getAndIncrement();
    }
    public void addReturnFunction(FunctionResult.Handler task, int messageId){
    	returnFunctions.put(messageId, task);
    }
    public WSConnection(String uri) throws URISyntaxException {
        super(new URI(uri));
        this.setEventHandler(new WebSocketEventHandler() {
            @Override
            public void onOpen() {
                //Log.i(TAG, "Opened");
            }

            @Override
            public void onMessage(WebSocketMessage message) {
                try {
                    JSONObject msgObj = new JSONObject(message.getText());
                    if(msgObj.has("replay")){//critical point TODO:use mutex or conditions to prevent concurrent problems
                    	if(returnFunctions.containsKey(msgObj.getInt("ID"))){
	                    	FunctionResult.Handler task = returnFunctions.get(msgObj.getInt("ID"));
	                    	if(!task.isDone()){
		                    	if(msgObj.getBoolean("success"))
		                    		task._onSuccess(msgObj.get("replay"));
		                    	else
		                    		task._onError(msgObj.get("replay"));
	                    	}
                    	}
                    }else{
	                    Class<?> c = Class.forName(WSClient.class.getCanonicalName()+ "$" + msgObj.getString("hub"));
	                    Method[] methods = c.getDeclaredMethods();
	                    String functionName = msgObj.getString("function").toUpperCase();
	                    for (Method m : methods) {
	                        if (m.getName().toUpperCase().equals(functionName)) {
	                        	int parametersLenght = m.getParameterTypes().length;
	                        	Object[] args = new Object[parametersLenght];
	                        	for( int i=0; i< parametersLenght; i++)
	                        		args[i] = msgObj.getJSONArray("args").get(i);
	                            m.invoke(null, args);
	                            return;
	                        }
	                    }
                    }
                } catch (Exception e) {
                	System.out.println("ERROR - "+e.toString());
                    //Log.e(TAG, "Error " + e.getMessage());
                }
            }

            @Override
            public void onError(IOException ex) {
                //Log.e(TAG, "Error " + ex.getMessage());
            }

            @Override
            public void onClose() {
                //Log.i(TAG, "Closed ");
            }

            @Override
            public void onPing() {
            }

            @Override
            public void onPong() {
            }
        });
    }
}