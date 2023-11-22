package com.example.demoiot;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;

import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.SeekBar;
import android.widget.Spinner;
import android.widget.TextView;

import com.github.angads25.toggle.widget.LabeledSwitch;
import com.google.android.material.snackbar.Snackbar;

import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallbackExtended;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.MqttPersistenceException;

import java.nio.charset.StandardCharsets;

public class MQTTController extends AppCompatActivity {
    private MQTTModel mqttModel;
    private TextView txtTemp, txtHumid, txtAI;
    private LabeledSwitch btnLED;
    private SeekBar btnFAN;

    private String frequency;
    private Spinner frequencySpinner;
    private Button submitButton;
    private Thread thread;
    private int isWaitingFromServer = 0;
    private String topicSent = "";
    private MqttMessage payloadSent;
    private String last_will_message = "default last will message";
    private boolean isConnected = false; // Connection to gateway

    private final int connectionTimeout = 60;
    private final int serverTimeout = 5;
    private boolean receiveConnectionStatus = false;
    private final Counter connectionCounter = new Counter(connectionTimeout);
    private final Counter serverCounter = new Counter(serverTimeout);
    private final int resend = 2;
    private int numResentServer = 0;


    // 2 - Hop Error Controller
    private final int gatewayTimeout = 7;
    private final Counter gatewayCounter = new Counter(gatewayTimeout);
    private int numResentGateway = 0;
    private String previousLed = "0";
    private String previousFan = "0";
    private String previousToggledItem = "";


    private void resetUI() {
        if (previousToggledItem.contains("led")) {
            displaySnackbar("Cannot change LED status");
            updateLED(previousLed);
        } else if (previousToggledItem.contains("fan")) {
            displaySnackbar("Cannot change FAN status");
            updateFan(previousFan);
        }
    }


    private void startThread() {
        thread = new Thread(new Runnable() {
            @Override
            public void run() {
                while (true) {
                    try {
                        if (isWaitingFromServer == 1) {
                            // Waiting from server
                            if (serverCounter.update()) {
                                if (numResentServer < resend) {
                                    numResentServer += 1;
                                    mqttModel.mqttAndroidClient.publish(topicSent, payloadSent);
                                } else {
                                    isWaitingFromServer = 0;
                                    Log.d("MQTT", "No response from server. Message rejected due to timeout");
                                    resetUI();
                                }
                            }
                        } else if (isWaitingFromServer == 2) {
                            // Waiting from gateway
                            if (gatewayCounter.update()) {
                                if (numResentGateway < resend) {
                                    numResentGateway += 1;
                                    mqttModel.mqttAndroidClient.publish(topicSent, payloadSent);
                                } else {
                                    isWaitingFromServer = 0;
                                    Log.d("MQTT", "No response from gateway. Message rejected due to timeout");
                                    resetUI();
                                }
                            }
                        }

                        // Check connection to gateway
                        if (isConnected) {
                            if (receiveConnectionStatus) {
                                connectionCounter.reset();
                                receiveConnectionStatus = false;
                            } else {
                                if (connectionCounter.update()) {
                                    Log.d("MQTT", "Gateway disconnected");
                                    modifyConnectStatus(false);
                                    displaySnackbar("Gateway has been disconnected: " + last_will_message);
                                    isConnected = false;
                                }
                            }
                        }

                        // Run each 1 second
                        Thread.sleep(1000);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    } catch (MqttPersistenceException e) {
                        throw new RuntimeException(e);
                    } catch (MqttException e) {
                        throw new RuntimeException(e);
                    }
                }
            }
        });
        thread.start();
    }

    private void displaySnackbar(String message) {
        Snackbar.make(findViewById(R.id.linear_layout), message, Snackbar.LENGTH_LONG).show();
    }

    private void modifyConnectStatus(boolean status) {
        ImageView dotIndicator = findViewById(R.id.dot_indicator);
        if (!status) {
            dotIndicator.setColorFilter(ContextCompat.getColor(this, R.color.red));
        } else {
            dotIndicator.setColorFilter(ContextCompat.getColor(this, R.color.green));
        }
    }


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Initialize view
        initializeView();
        // Initialize model
        startMQTT();
        // Initialize background thread
        startThread();
    }


    private void initializeView() {
        setContentView(R.layout.activity_main);

        // Set view elements
        txtTemp = findViewById(R.id.txtTemperature);
        txtHumid = findViewById(R.id.txtHumidity);
        btnLED = findViewById(R.id.btnLED);
        btnFAN = findViewById(R.id.btnFan);
        txtAI = findViewById(R.id.txtAI);
        frequencySpinner = findViewById(R.id.frequency_spinner);
        submitButton = findViewById(R.id.submit_button);
        modifyConnectStatus(false);

        // Selection button
        ArrayAdapter<CharSequence> adapter = ArrayAdapter.createFromResource(this, R.array.options_array, android.R.layout.simple_spinner_item);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        frequencySpinner.setAdapter(adapter);
        submitButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                frequency = frequencySpinner.getSelectedItem().toString();
                if (frequency.contains("30s")) {
                    frequency = "30";
                } else if (frequency.contains("1m")) {
                    frequency = "60";
                } else if (frequency.contains("2m")) {
                    frequency = "120";
                } else if (frequency.contains("5m")) {
                    frequency = "300";
                }

                Log.d("MQTT", "Frequency change to " + frequency);
                sendDataMQTT("KanNan312/feeds/iot.frequency", frequency);
            }
        });

        // LED button
        btnLED.setOnToggledListener((labeledSwitch, isOn) -> {
            if (isOn) {
                sendDataMQTT("KanNan312/feeds/iot.led", "1");
            } else {
                sendDataMQTT("KanNan312/feeds/iot.led", "0");
            }
            previousToggledItem = "led";
        });

        // Fan button
        btnFAN.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar seekBar, int i, boolean b) {
                previousToggledItem = "fan";
                sendDataMQTT("KanNan312/feeds/iot.fan", Integer.toString(i));
            }

            @Override
            public void onStartTrackingTouch(SeekBar seekBar) {

            }

            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {

            }
        });
    }

    private void startMQTT() {
        mqttModel = new MQTTModel(this);
        mqttModel.setCallback(new MqttCallbackExtended() {
            @Override
            public void connectComplete(boolean reconnect, String serverURI) {
                Log.d("MQTT", "Connected!");
            }

            @Override
            public void connectionLost(Throwable cause) {
                Log.d("MQTT", "Connection lost!");
            }

            @Override
            public void deliveryComplete(IMqttDeliveryToken token) {
                Log.d("MQTT", "Delivery completed!");
            }

            @Override
            public void messageArrived(String topic, MqttMessage message) throws Exception {
                String message_txt = message.toString();
                Log.w("MQTT", topic + "***" + message_txt);

                String[] parts = message_txt.split(":");
                String header = parts[0];
                String payload = parts[1];
                // ACK from server
                if (header.contains("app") && isWaitingFromServer == 1) {
                    isWaitingFromServer = 2;
                    Log.d("MQTT", "Receive ACK from server. Waiting for gateway...");
                } else if (header.contains("gw")) {
                    if (topic.contains("iot.ack") && isWaitingFromServer == 2) {
                        // ACK from gateway: set flag
                        isWaitingFromServer = 0;
                        Log.d("MQTT", "Receive ACK from gateway. Finished!");
                        String previousStatus = payloadSent.toString().split(":")[1];
                        if (previousToggledItem.contains("led")) {
                            previousLed = previousStatus;
                        } else if (previousToggledItem.contains("fan")) {
                            previousFan = previousStatus;
                        }
                    } else if (topic.contains("iot.connection")) {
                        if (payload.contains("will")) {
                            last_will_message = payload.split("_")[1];
                        } else if (payload.contains("live_on")) {
                            if (!isConnected) {
                                displaySnackbar("Gateway connected");
                                isConnected = true;
                                modifyConnectStatus(true);
                            }
                            receiveConnectionStatus = true;
                        } else if (payload.contains("uart_off")) {
                            displaySnackbar("Uart disconnected");
                        } else if (payload.contains("uart_on")) {
                            displaySnackbar("Uart connected");
                        }
                    }
                    if (topic.contains("iot.temperature")) {
                        updateTemperature(payload);
                    } else if (topic.contains("iot.humidity")) {
                        updateHumidity(payload);
                    } else if (topic.contains("iot.led")) {
                        updateLED(payload);
                    } else if (topic.contains("iot.fan")) {
                        updateFan(payload);
                    } else if (topic.contains("iot.human-detect")) {
                        updateAI(payload);
                    }
                }
            }
        });
    }

    public void sendDataMQTT(String topic, String value) {
        if (isWaitingFromServer != 0) {
            return;
        }
        value = "app:" + value;
        MqttMessage msg = new MqttMessage();
        msg.setId(1234);
        msg.setQos(0);
        msg.setRetained(false);

        byte[] b = value.getBytes(StandardCharsets.UTF_8);
        msg.setPayload(b);

        try {
            Log.d("MQTT", "Send message to server: " + value);
            mqttModel.mqttAndroidClient.publish(topic, msg);
            isWaitingFromServer = 1;
            numResentServer = 0;
            topicSent = topic;
            payloadSent = msg;
        } catch (MqttException e) {
            Log.e("MQTT", "Failed to publish message: " + e.getMessage(), e);
        }
    }


    public void updateTemperature(String value) {
        txtTemp.setText(value + "°C");
    }

    public void updateHumidity(String value) {
        txtHumid.setText(value + "%");
    }

    public void updateAI(String value) {
        txtAI.setText(value);
    }

    public void updateFan(String value) {
        btnFAN.setProgress(Integer.parseInt(value));
    }

    public void updateLED(String value) {
        btnLED.setOn(value.equals("1"));
    }
}

