from controller import SerialDataHandler
from utils import Counter, is_valid_sensor_value
# from utils.message_handler import MessageHandler
import cv2
import time, sys, threading
import logging
logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO)

class GatewayController(threading.Thread):
  def __init__(self, app, model, ai_recognizer, ai_freq=60, sensor_freq=30, status_freq=20, sleep=1, will='', resend=2, timeout=7):
    super().__init__()

    # app
    app.add_controller(self)
    self.app = app

    # create and connect to mqtt client
    model.add_controller(self)
    self.model = model
    self.client, self.aio_feed_ids = self.model.client, self.model.aio_feed_ids
    self.subscribed_feeds = 0
    self.__connectClient()

    # ai model
    self.ai_recognizer = ai_recognizer

    # create serial data handler and uart connection checker
    self.ser = SerialDataHandler(self.process_mcu_message)
    self.uart_connected = True
    if not self.ser.port:
      logging.warning("WARNING: uart is not connected")
      self.uart_connected = False

    self.uart_reconnect = 0
    self.uart_max_reconnect = 10
    self.uart_status_sent = False
    
    # sensor state recorded by gateway
    self.sensor_states = {"temperature": -1, "humidity": -1} 

    # set up webcam for AI Inference
    self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    # set up data sending frequencies
    self.status_counter = Counter(status_freq)
    self.ai_counter = Counter(ai_freq)
    self.sensor_counter = Counter(sensor_freq)
    self.sleep = sleep

    # for stop and wait protocol
    self.resend = resend
    self.timeout = timeout

    self.server_messages = []
    self.uart_messages = []

    self.server_lock = threading.Lock()
    self.uart_lock = threading.Lock()

    # last will message
    self.will = will
    self.last_will_message()

  # connect client and set up the last will message
  def __connectClient(self):
    # start the connection
    self.client.connect()
    # create background thread to listen to adafruit info
    self.client.loop_background()

  def last_will_message(self):
    # wail until all feeds have been subscribed
    while self.subscribed_feeds < len(self.aio_feed_ids):
      pass
    # last will message
    self.send_message_to_server("iot.connection", f"will_{self.will}")
  

  def AI_inference(self):
    # do the AI inference
    ret, frame = self.camera.read()
    if ret:
      # make detection, update dashboard, display LCD and send result to server
      results = self.ai_recognizer.detect(frame)
      if len(results) == 0:
        display = "Welcome"
        info = "No people"
      else:
        name, mask = results[0]
        remind = "Welcome to HCMUT library!" if mask else "Please wear your mask!"
        display = f"Hi {name}! {remind}"
        info = f"{name}, wearing mask" if mask else f"{name}, no mask"

      # send message to server, update dashboard and display uart
      self.send_message_to_server("iot.human-detect", info)
      self.app.update_AI(info)

      if self.uart_connected:
        self.send_message_to_mcu('D', display)

        

  # send message to server using the stop and wait protocol
  def send_message_to_server(self, feed_id, payload):
    # loop through all the inwaiting message
    for message in self.server_messages:
      if message["feed_id"] == feed_id:
        logging.debug(f"Previous data is being sent to server: {feed_id}")
        return

    logging.info(f"Sending data to server: {feed_id}, {payload}")
    # append "gate way" prefix to the payload
    payload = "gw:" + payload
    self.client.publish(feed_id, payload)
    # add a new message error controller
    message = {
      "feed_id": feed_id,
      "payload": payload,
      "counter": Counter(self.timeout),
      "num_resent": 0
    }
    self.server_messages.append(message)


  # send sensor data to server when invoked
  def send_sensor_data(self):
    temp = self.sensor_states["temperature"]
    humid = self.sensor_states["humidity"]
    if temp != -1:
      logging.info(f"Updating temperature to server: {temp}")
      self.send_message_to_server("iot.temperature", temp)
    if humid != -1:
      logging.info(f"Updating humidity to server: {humid}")
      self.send_message_to_server("iot.humidity", humid)

  # send data to mcu
  def send_message_to_mcu(self, cmd, payload):
    request = cmd + ':' + str(payload)

    # loop through all the inwaiting message
    for message in self.uart_messages:
      if message["cmd"] == cmd:
        logging.debug(f"Previous data is being sent to MCU: {cmd}")
        return

    logging.info(f"Sending request to MCU: {request}")
    self.ser.write_data(request)
    message = {
      "request": request,
      "cmd": cmd,
      "counter": Counter(self.timeout),
      "num_resent": 0
    }
    self.uart_messages.append(message)


  # process message from server
  def process_server_message(self, feed_id, payload):
    logging.debug(f"Received message from server: {feed_id}: {payload}")
    # print(payload)
    header, payload = payload.split(':')
    # if message is from gw, update ACK flag
    if header == "gw":
      # loop through the list of messages and delete the one with the same feed_id as ACK message
      with self.server_lock:
        message_idx = 0
        while message_idx < len(self.server_messages):
          message = self.server_messages[message_idx]
          if message["feed_id"] == feed_id:
            logging.info(f"Received ACK from server: {feed_id}")
            del self.server_messages[message_idx]
          else:
            message_idx += 1
        
    
    # if message if from the app, send ACK and process
    elif header == "app":
      # send ACK
      self.client.publish("iot.ack", "gw:1")

      # process payload and send command to uart
      if self.uart_connected:
        if feed_id == "iot.led":
          cmd = 'L'
          # send request to MCU and update dashboard
          # self.send_message_to_mcu(cmd, payload)
          self.app.update_LED(payload)

        elif feed_id == "iot.fan":
          cmd = 'F'
          mcu_payload = int(payload) * 33
          # send request to MCU and update dashboard
          # self.send_message_to_mcu(cmd, mcu_payload)
          self.app.update_fan(payload)
        
        elif feed_id == "iot.frequency":
          logging.info(f"Sensor sending frequency updated: {payload} seconds")
          self.sensor_counter = Counter(n=int(payload))
        
  # process uart message
  def process_mcu_message(self, data):
    logging.debug(f"Received message from MCU: {data}")
    if "ACK" in data:
      cmd = data.split("_")[1]
      # loop through the list of messages and delete the one with the same cmd as the ACK message
      with self.uart_lock:
        message_idx = 0
        while message_idx < len(self.uart_messages):
          message = self.uart_messages[message_idx]
          if message["cmd"] == cmd:
            logging.info(f"Received ACK from MCU: {cmd}")
            del self.uart_messages[message_idx]
          else:
            message_idx += 1

    else:
      _, cmd, payload = data.split(':')

      # update temperature and discard the out of range value, also reject duplicate value
      if cmd == "T":
        if is_valid_sensor_value("T", payload) and payload != self.sensor_states["temperature"]:
          logging.debug(f"Temperature read: {payload}")
          # send ACK to MCU and update dashboard temperature
          self.ser.write_data("ACK_T")
          self.app.update_temperature(payload)
        
          # update temperature state to send to server later
          self.sensor_states["temperature"] = payload

        elif not is_valid_sensor_value("T", payload):
          logging.debug(f"Temperature value {payload} out of range. Reject")
        

      # update humidity and discard the out of range value, also reject the duplicate values
      elif cmd == "H":
        if is_valid_sensor_value("H", payload) and payload != self.sensor_states["humidity"]:
          logging.debug(f"Humidity read: {payload}")
          # send ACK to MCU and update dashboard temperature
          self.ser.write_data("ACK_H")
          self.app.update_humidity(payload)

          # update humidity state to send to server later
          self.sensor_states["humidity"] = payload
        
        elif not is_valid_sensor_value("H", payload):
          logging.debug(f"Humidity value {payload} out of range. Reject")

  def app_control_LED(self, value):
    # send request to MCU and server
    if self.uart_connected:
      self.send_message_to_mcu('L', value)

    self.send_message_to_server("iot.led", str(value))
  
  def app_control_fan(self, value):
    mcu_payload = int(value) * 33
    # send request to MCU and server
    if self.uart_connected:
      print('Control fan:', value)
      self.send_message_to_mcu('F', mcu_payload)

    self.send_message_to_server("iot.fan", str(value))
  
  def app_control_frequency(self, value):
    self.sensor_counter = Counter(int(value))

  def check_uart_connection(self):
    # try to reconnect
    connected = self.ser.is_serial_connected()
    # if the uart is reconnected
    if connected:
      self.uart_connected = True
      # if the disconnect message has been sent, send a reconnected status to server, else just set the flag
      if self.uart_status_sent:
        logging.info("Uart has been reconnected. Sending status to server...")
        self.send_message_to_server("iot.connection", "uart_on")
        self.uart_reconnect = 0
        self.uart_status_sent = False
    
    # if the uart is still disconnected:
    else:
      # if the status is not sent to server and the max number of reconnections reached, send a disconnect status
      if not self.uart_status_sent:
        self.uart_reconnect += 1
        if self.uart_reconnect >= self.uart_max_reconnect:
          logging.info("Uart cannot reconnect after some trials. Sending status to server...")
          self.send_message_to_server("iot.connection", "uart_off")
          self.uart_status_sent = True

  def control_server_messages(self):
    # one-hop error controller for all the inwaiting server messages
    with self.server_lock:
      message_idx = 0
      while message_idx < len(self.server_messages):
        message = self.server_messages[message_idx]
        # if timeout, resend
        if message["counter"].update():
          if message["num_resent"] < self.resend:
            message["num_resent"] += 1
            logging.debug(f"Resending message to server {message['num_resent']}th time: {message['feed_id']}")
            self.client.publish(message["feed_id"], message["payload"])
            message_idx += 1

          # reject the message due to timeout
          else:
            logging.info(f"Sending to server rejected due to timeout: {message['feed_id']}")
            del self.server_messages[message_idx]
        else:
          message_idx += 1

  def control_mcu_messages(self):
    # one-hop error controller for all the inwaiting mcu messages
    with self.uart_lock:
      message_idx = 0
      while message_idx < len(self.uart_messages):
        message = self.uart_messages[message_idx]
        # if timeout, resend
        if message["counter"].update():
          if message["num_resent"] < self.resend and self.uart_connected:
            message["num_resent"] += 1
            logging.debug(f"Resending message to MCU {message['num_resent']}th time: {message['cmd']}")
            self.ser.write_data(message["request"])
            message_idx += 1

          # reject the message due to timeout
          else:
            logging.info(f"Sending to uart rejected due to timeout: {message['cmd']}")
            del self.uart_messages[message_idx]
        else:
          message_idx += 1

  def run(self):
    # main thread loop
    while True:
      try:
        # check uart status repeatively every 1s if uart is disconnected
        if not self.uart_connected:
          self.check_uart_connection()

        # update status to server
        if self.status_counter.update():
          self.send_message_to_server("iot.connection", "live_on")

        # read serial for sensor data and ack
        if self.uart_connected:
          logging.debug('Reading Serial ...')
          try:
            self.ser.read_serial()
          except Exception as e:
            print(e)
            logging.debug("Detect uart disconnection")
            self.uart_connected = False
        
        # send sensor data to server
        if self.sensor_counter.update():
          self.send_sensor_data()

        # do the AI inference
        if self.ai_counter.update():
          self.AI_inference()
        
        # one-hop error controller for all the inwaiting server messages
        self.control_server_messages()
        
        # one hop error controller for MCU
        self.control_mcu_messages()

        # sleep a while
        time.sleep(self.sleep)
      
      except Exception as e:
        logging.error(e)
        # release the camera
        self.camera.release()
        cv2.destroyAllWindows()
        break