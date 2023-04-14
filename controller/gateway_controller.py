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
  def __init__(self, app, model, ai_freq=60, sensor_freq=30, status_freq=20, sleep=1, will=''):
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
    self.resend = 2
    self.timeout = 5

    self.waiting_from_server = False
    self.waiting_from_uart = False
    self.payload_sent = None
    self.feed_id_sent = None
    self.uart_request_sent = None
    self.num_resent_server = 0
    self.num_resent_uart = 0

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
      result = self.model.mask_detect(frame)
      self.app.update_AI(result)

      if self.uart_connected:
        display = "Please wear your mask" if result == "No Mask" else "Welcome"
        self.send_message_to_mcu(f"D:{display}")

      self.send_message_to_server("iot.human-detect", result)

  # send message to server using the stop and wait protocol
  def send_message_to_server(self, feed_id, payload):
    if self.waiting_from_server:
      logging.debug("Waiting for server response from previous message")
      return

    logging.info(f"Sending data to server: {feed_id}, {payload}")
    # append "gate way" prefix to the payload
    payload = "gw:" + payload
    self.client.publish(feed_id, payload)
    # for error controller
    self.waiting_from_server = True
    self.server_counter = Counter(self.timeout)
    self.payload_sent = payload
    self.feed_id_sent = feed_id
    self.num_resent_server = 0

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
  def send_message_to_mcu(self, request):
    print(self.waiting_from_uart)
    if self.waiting_from_uart:
      logging.debug("Previous message is sending to MCU")
      return

    logging.info(f"Sending request to MCU: {request}")
    self.ser.write_data(request)
    self.waiting_from_uart = True
    self.uart_request_sent = request
    self.uart_counter = Counter(self.timeout)
    self.num_resent_uart = 0


  # process message from server
  def process_server_message(self, feed_id, payload):
    logging.debug(f"Received message from server: {feed_id}: {payload}")
    # print(payload)
    header, payload = payload.split(':')
    # if message is from gw, update ACK flag
    if header == "gw":
      if self.waiting_from_server:
        self.waiting_from_server = False
        logging.debug(f"Received response from server: {feed_id}")
    
    # if message if from the app, send ACK and process
    elif header == "app":
      # send ACK
      self.send_message_to_server("iot.ack", "1")

      # process payload and send command to uart
      if self.uart_connected:
        if feed_id == "iot.led":
          uart_request = f"L:{payload}"
          # send request to MCU and update dashboard
          self.send_message_to_mcu(uart_request)
          self.app.update_LED(payload)

        elif feed_id == "iot.fan":
          uart_request = f"F:{int(payload) * 33}"
          # send request to MCU and update dashboard
          self.send_message_to_mcu(uart_request)
          self.app.update_fan(payload)
        
        elif feed_id == "iot.frequency":
          logging.info(f"Sensor sending frequency set to {payload} seconds")
          self.sensor_counter = Counter(n=int(payload))
        
  # process uart message
  def process_mcu_message(self, data):
    logging.info(f"Received message from MCU: {data}")
    if data == "ACK":
      # receive ACK message from MCU
      if self.waiting_from_uart:
        self.waiting_from_uart = False
        logging.info(f"Received response from MCU")
    else:
      _, cmd, payload = data.split(':')

      # update temperature and discard the out of range value, also reject duplicate value
      if cmd == "T" and is_valid_sensor_value("T", payload) and payload != self.sensor_states["temperature"]:
        logging.info(f"Temperature read: {payload}")
        # send ACK to MCU and update dashboard temperature
        self.ser.write_data("ACK_T")
        self.app.update_temperature(payload)
        
        # update temperature state to send to server later
        self.sensor_states["temperature"] = payload
        

      # update humidity and discard the out of range value, also reject the duplicate values
      elif cmd == "H" and is_valid_sensor_value("H", payload) and payload != self.sensor_states["humidity"]:
        logging.info(f"Humidity read: {payload}")
        # send ACK to MCU and update dashboard temperature
        self.ser.write_data("ACK_H")
        self.app.update_humidity(payload)

        # update humidity state to send to server later
        self.sensor_states["humidity"] = payload

  def app_control_LED(self, value):
    uart_request = f"L:{value}"
    # send request to MCU and server
    if self.uart_connected:
      self.send_message_to_mcu(uart_request)

    self.send_message_to_server("iot.led", str(value))
  
  def app_control_fan(self, value):
    uart_request = f"F:{int(value) * 33}"
    # send request to MCU and server
    if self.uart_connected:
      self.send_message_to_mcu(uart_request)

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
            logging.info("Detect uart disconnection")
            self.uart_connected = False
        
        # send sensor data to server
        if self.sensor_counter.update():
          self.send_sensor_data()

        # do the AI inference
        if self.ai_counter.update():
          self.AI_inference()
        
        # one-hop error controller for server
        if self.waiting_from_server:
          # if timeout, resend
          if self.server_counter.update():
            if self.num_resent_server < self.resend:
              self.num_resent_server += 1
              self.client.publish(self.feed_id_sent, self.payload_sent)
              logging.info(f"Resending message to server: {self.num_resent_server}")
            else:
              self.waiting_from_server = False
              logging.info("Sending to server rejected due to timeout")
        
        # one hop error controller for MCU
        if self.waiting_from_uart:
          # if timeout, resend
          if self.uart_counter.update():
            if self.num_resent_uart < self.resend and self.uart_connected:
              self.num_resent_uart += 1
              logging.info(f"Resending message to MCU: {self.num_resent_uart}")
              self.ser.write_data(self.uart_request_sent)

            else:
              self.waiting_from_uart = False
              logging.info("Sending to uart rejected due to timeout")

        # sleep a while
        time.sleep(self.sleep)
      
      except Exception as e:
        logging.error(e)
        # release the camera
        self.camera.release()
        cv2.destroyAllWindows()
        break