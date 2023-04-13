from controller import SerialDataHandler
from utils import Counter, is_valid_sensor_value
# from utils.message_handler import MessageHandler
import cv2
import time, sys, threading
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

class GatewayController(threading.Thread):
  def __init__(self, app, model, ai_freq=20, sensor_freq=20, status_freq=10, sleep=1, will=''):
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

    # create serial data handler
    self.ser = SerialDataHandler(3, self.process_mcu_message)
    self.uart_connected = False
    if not self.ser.port:
      logging.warning("WARNING: uart is not connected")

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
  
  # check uart_connection 
  def check_uart_connection(self):
    # check connection and try to reconnect
    if self.ser.is_serial_connected():
      if not self.uart_connected:
        self.uart_connected = True
        self.send_message_to_server("iot.connection", "uart_on")
      return True
    # if uart is disconnected, send warning
    else:
      if self.uart_connected:
        self.uart_connected = False
        self.send_message_to_server("iot.connection", "uart_off")
      return False

  def AI_inference(self):
    # do the AI inference
    ret, frame = self.camera.read()
    if ret:
      # make detection, update dashboard, display LCD and send result to server
      result = self.model.mask_detect(frame)
      self.app.update_AI(result)

      if self.check_uart_connection():
        display = "Please wear your mask" if result == "No Mask" else "Welcome"
        self.send_message_to_mcu(f"D:{display}")

      self.send_message_to_server("iot.human-detect", result)

  # send data to server using the stop and wait protocol
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



  # send data to mcu
  def send_message_to_mcu(self, request):
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
    header, payload = payload.split(':')
    # if message is from gw, update ACK flag
    if header == "gw" and self.waiting_from_server:
      self.waiting_from_server = False
      logging.info(f"Received response from server: {feed_id}")
    
    # if message if from the app, send ACK and process
    elif header == "app":
      # send ACK
      self.send_message_to_server("iot.ack", "1")

      # process payload and send command to uart
      if self.check_uart_connection():
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
          self.sensor_counter = Counter(n=int(payload))
        
  # process uart message
  def process_mcu_message(self, data):
    logging.debug(f"Received message from MCU: {data}")
    if data == "ACK" and self.waiting_from_uart:
      # receive ACK message from MCU
      self.waiting_from_uart = False
      logger.info(f"Received response from MCU")
    else:
      _, cmd, payload = data.split(':')
      # send ACK to MCU when sensor data is received
      self.ser.write_data("ACK")

      # update temperature and discard the out of range value
      if cmd == "T" and is_valid_sensor_value("T", payload):
        # update dashboard UI and send server message
        self.app.update_temperature(payload)
        self.send_message_to_server("iot.temperature", payload)
      # update humidity and discard the out of range value
      elif cmd == "H" and is_valid_sensor_value("H", payload):
        self.app.update_humidity(payload)
        self.send_message_to_server("iot.humidity", payload)

  def app_control_LED(self, value):
    uart_request = f"L:{value}"
    # send request to MCU and server
    if self.check_uart_connection():
      self.send_message_to_mcu(uart_request)

    self.send_message_to_server("iot.led", str(value))
  
  def app_control_fan(self, value):
    uart_request = f"F:{value * 33}"
    # send request to MCU and server
    if self.check_uart_connection():
      self.send_message_to_mcu(uart_request)

    self.send_message_to_server("iot.fan", str(value))
  
  def app_control_frequency(self, value):
    self.sensor_counter = Counter(int(value))

  def run(self):
    # main thread loop
    while True:
      try:
        # update status to server
        if self.status_counter.update():
          self.send_message_to_server("iot.connection", "live_on")

        # update sensor value to server
        if self.sensor_counter.update():
          if self.check_uart_connection():
            logging.debug('Reading Serial ...')
            self.ser.read_serial(self.client)

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
            if self.num_resent_uart < self.resend:
              self.num_resent_uart += 1
              self.ser.write_data(self.uart_request_sent)
              logging.info(f"Resending message to uart: {self.num_resent_uart}")
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