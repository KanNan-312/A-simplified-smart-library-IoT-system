from model.mqtt import create_mqtt_client
from controller.uart import SerialDataHandler
from utils.counter import Counter
# from utils.message_handler import MessageHandler
from model.mask_detection.model import MaskDetector
import cv2
import time, sys, threading

class GatewayController:
  def __init__(self, adafruit_json_key, ai_weights, ai_labels, ai_skip, sleep):
    # create and connect mqtt client
    self.client, self.aio_feed_ids = create_mqtt_client(adafruit_json_key)
    self.__connectClient()
    # create serial data handler
    self.ser = SerialDataHandler(self.processSerialMessage)
    # set up webcam and AI model
    self.camera = cv2.VideoCapture(0)
    self.detector = MaskDetector(weight=ai_weights, label=ai_labels)
    self.ai_counter = Counter(ai_skip)
    # time sleep
    self.sleep = sleep
    # message handler
    # self.mess_handler = MessageHandler()

    # for stop and wait protocol
    self.resend = 2
    self.timeout = 4
    self.server_ack = threading.Event()
    self.feed_id_sent = None
    self.payload_sent = None
    self.uart_ack = threading.Event()

    self.server_num_resent = 0
    self.uart_num_resent = 0

  # send data to server using the stop and wait protocol
  def sendMessageToServer(self, feed_id, payload):
    print("Sending data to server ...")
    self.feed_id_sent = feed_id
    self.payload_sent = payload
    self.client.publish(feed_id, payload)
    self.server_ack.wait(self.timeout)

    while not self.server_ack.isSet() and self.server_num_resent < self.resend:
      print("Resending data to server ...")
      self.client.publish(feed_id, payload)
      self.server_num_resent += 1
      self.server_ack.wait(self.timeout)
    
    if not self.server_ack.isSet():
      print("Data rejected due to timeout ...")
    # reset flag and numresent
    self.server_ack.clear()
    self.server_num_resent = 0
  
  def sendMessageToMCU(self, request):
    print("Sending request to MCU ...")
    self.ser.writeData(request)
    self.uart_ack.wait(self.timeout)

    while not self.uart_ack.isSet() and self.uart_num_resent < self.resend:
      print("Resending request to MCU ...")
      self.ser.writeData(request)
      self.uart_num_resent += 1
      self.uart_ack.wait(self.timeout)
    
    if not self.uart_ack.isSet():
      print("Request rejected due to timeout ...")
    # reset flag and numresent
    self.uart_ack.clear()
    self.uart_num_resent = 0
  
  def run(self):
    # main thread loop
    try:
      while True:
        if self.ser.isSerialConnected():
          # print('Reading Serial ...')
          self.ser.readSerial(self.client)
        
        if self.ai_counter.update():
          # do the AI inference
          ret, frame = self.camera.read()
          if ret:
            result = self.detector.predict(frame)
            self.sendMessageToServer("iot.human-detect", result)

            if self.ser.isSerialConnected():
              self.sendMessageToMCU(f"D:{result}")
        
        time.sleep(self.sleep)
    except Exception as e:
      print(e)
      # release the camera
      self.camera.release()
      cv2.destroyAllWindows()

  def __connectClient(self):
    self.client.on_connect = self.connected
    self.client.on_disconnect = self.disconnected
    self.client.on_message = self.message
    self.client.on_subscribe = self.subscribe
    # start the connection
    self.client.connect()
    # create background thread to listen to adafruit info
    self.client.loop_background()

  def connected(self, client):
    print("Connected successfully!")
    [self.client.subscribe(feed_id) for feed_id in self.aio_feed_ids]

  def subscribe(self, client , userdata , mid , granted_qos):
    print("Subscribed successfully!")

  def disconnected(self, client):
    print("Disconnected ...")
    sys.exit(1)

  def message(self, client, feed_id, payload):
    print(f"Received message from server: {feed_id}: {payload}")
    # check server ACK:
    if feed_id == self.feed_id_sent and payload == self.payload_sent:
      self.server_ack.set()
      self.feed_id_sent = None
      self.payload_sent = None

    # send serial request
    if self.ser.isSerialConnected():
      uart_request = None
      if feed_id == "iot.led":
        uart_request = f"L:{payload}"
      elif feed_id == "iot.relay":
        uart_request = f"R:{payload}"
      elif feed_id == "iot.fan":
        uart_request = f"F:{int(payload) * 33}"
      
      # send request to MCU
      if uart_request:
        self.sendMessageToMCU(uart_request)
          

  def processSerialMessage(self, data):
    data = data.replace("!", "")
    data = data.replace("#", "")
    print(f"Received message from MCU: {data}")
    if data == "ACK":
      # receive ACK message from MCU
      self.uart_ack.set()
    else:
      splitData = data.split(':')
      # send ACK to MCU when sensor data is received
      self.ser.writeData("ACK")

      # temperature
      if splitData[1] == "T":
        self.sendMessageToServer("iot.temperature", splitData[2])
      # humidity
      elif splitData[1] == "H":
        self.sendMessageToServer("iot.humidity", splitData[2])
