## About this project
This is the implementation of a simplified smart IoT system.

There are two main components:
1. Python gateway: the gateway is directly connected to the sensors in order to read sensor data and send control to devices. Data read from the sensor is sent to the Adafruit.io broker server.
2. Android application: This application is connected to the server to track the sensor value in real time. The admin can also control devices remotely from the application.

## Prerequesite
1. A [YoloBit](https://ohstem.vn/hoc-lap-trinh-iot-voi-mach-yolobit/) device or any orther microcontroller which can transfer serial data between sensors and gatewat.
2. A laptop PC with Python and Android SDK installed.
3. An account on [Adafruit](https://io.adafruit.com/) with Adafruit key (This serves as an intermediate party to store sensor data. You can implement your own broker server if necessary).

## Set up feeds on Adafruit server
You need to create a channel for each sensor type on the Adafruit server. To run our code, create 8 feeds with the following name: ack, connection, fan, frequency, human-detect, humidity, led, temperature. Put them into a folder named "iot" to make sure their ids are: "iot.ack", "iot.connection", "iot.fan", etc. respectively.

To run the code you will have to paste the id of all feeds and your credential key into the file "adafruit_key.json"

## Load the code into microcontroller
1. We provided the code for dealing with serial data in folder [yolobit](yolobit). If you wish to use another type of microcontroller (or microprocessor), you need to write your own code. Then load the code into your micocontroller.
2. We used 4 types of sensors: a fan, a LED, an LCD screen, a DHT20 for reading temperature and humidity. All these sensors are provided in the [YoloBit](https://ohstem.vn/hoc-lap-trinh-iot-voi-mach-yolobit/) kit when you purchased.


## To run the Python Gateway
1. Create environment
```
    conda create -n myenv
    conda activate myend
```
2. Install dependencies
```
    pip install -r requirements.txt
```

## To run the Android application
As I am not an expert in Android development, I cannot provide details about the application. All the thing you need is located inside the folder [app](app).
1. Install Android Studio/VSCode
2. Load the project from the app folder.

## AI face mask detector
We also provide the code for FaceID detection. If you want to build your own database, replace the folder [database](model/face_mask_recognition/database). Your name and your mask status (wearing mask or not) will be displayed in the LCD screen when you run the whole system.








