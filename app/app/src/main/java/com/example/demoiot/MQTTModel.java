package com.example.demoiot;
import android.content.Context;
import android.util.Log;

import org.eclipse.paho.android.service.MqttAndroidClient;
import org.eclipse.paho.client.mqttv3.DisconnectedBufferOptions;
import org.eclipse.paho.client.mqttv3.IMqttActionListener;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.IMqttToken;
import org.eclipse.paho.client.mqttv3.MqttCallbackExtended;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;


public class MQTTModel {
    public MqttAndroidClient mqttAndroidClient;

    public final String[] arrayTopics = {
//            "phattt/feeds/iot.connection",
            "KanNan312/feeds/iot.fan",
            "KanNan312/feeds/iot.temperature",
            "KanNan312/feeds/iot.humidity",
            "KanNan312/feeds/iot.human-detect",
            "KanNan312/feeds/iot.led",
            "KanNan312/feeds/iot.connection",
            "KanNan312/feeds/iot.ack",
    };
    final String clientId = "123456789";
    final String username = "KanNan312";
    final String password = "aio_HhFM57STc2eq3KMsnRNsI6W22Smd";
//    final String username = "phattt";
//    final String password = "aio_klNL99Soz6VBojQ9AUbNCnUcGRZ4";

    final String serverUri = "tcp://io.adafruit.com:1883";

    public MQTTModel(Context context){
        mqttAndroidClient = new MqttAndroidClient(context, serverUri, clientId);
        mqttAndroidClient.setCallback(new MqttCallbackExtended() {
            @Override
            public void connectComplete(boolean b, String s) {
                Log.w("MQTT", s);
            }

            @Override
            public void connectionLost(Throwable throwable) {

            }

            @Override
            public void messageArrived(String topic, MqttMessage mqttMessage) throws Exception {
                Log.w("MQTT", mqttMessage.toString());
            }

            @Override
            public void deliveryComplete(IMqttDeliveryToken iMqttDeliveryToken) {

            }
        });
        connect();
    }

    public void setCallback(MqttCallbackExtended callback) {
        mqttAndroidClient.setCallback(callback);
    }

    private void connect(){
        MqttConnectOptions mqttConnectOptions = new MqttConnectOptions();
        mqttConnectOptions.setAutomaticReconnect(true);
        mqttConnectOptions.setCleanSession(false);
        mqttConnectOptions.setUserName(username);
        mqttConnectOptions.setPassword(password.toCharArray());

        try {

            mqttAndroidClient.connect(mqttConnectOptions, null, new IMqttActionListener() {
                @Override
                public void onSuccess(IMqttToken asyncActionToken) {

                    DisconnectedBufferOptions disconnectedBufferOptions = new DisconnectedBufferOptions();
                    disconnectedBufferOptions.setBufferEnabled(true);
                    disconnectedBufferOptions.setBufferSize(100);
                    disconnectedBufferOptions.setPersistBuffer(false);
                    disconnectedBufferOptions.setDeleteOldestMessages(false);
                    mqttAndroidClient.setBufferOpts(disconnectedBufferOptions);
                    subscribeToTopic();
                }

                @Override
                public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                    Log.w("MQTT", "Failed to connect to: " + serverUri + exception.toString());
                }
            });


        } catch (MqttException ex){
            ex.printStackTrace();
        }
    }

    private void subscribeToTopic() {
        for(int i = 0; i < arrayTopics.length; i++) {
            final String topicName = arrayTopics[i]; // Store the topic name in a final variable for use in the log message
            try {
                mqttAndroidClient.subscribe(topicName, 0, null, new IMqttActionListener() {
                    @Override
                    public void onSuccess(IMqttToken asyncActionToken) {
                        Log.d("MQTT", "Subscribed to topic: " + topicName);
                    }

                    @Override
                    public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                        Log.d("MQTT", "Failed to subscribe to topic: " + topicName);
                    }
                });

            } catch (MqttException ex) {
                System.err.println("Exception subscribing");
                ex.printStackTrace();
            }
        }
    }

}
