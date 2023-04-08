from Adafruit_IO import MQTTClient
from model.mask_detection.model import MaskDetector
import json
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

class GatewayModel():
  def __init__(self, adafruit_json_key, ai_weights, ai_labels):
    self.client, self.aio_feed_ids = self.__create_mqtt_client(adafruit_json_key)
    # add callback function
    self.client.on_connect = self.connected
    self.client.on_disconnect = self.disconnected
    self.client.on_message = self.message
    self.client.on_subscribe = self.subscribe

    # initialize ai model
    self.detector = MaskDetector(weight=ai_weights, label=ai_labels)

  def add_controller(self, controller):
    self.controller = controller

  def mask_detect(self, frame):
    return self.detector.predict(frame)

  def __create_mqtt_client(self, json_key):
    with open(json_key, "r") as f:
      data = json.load(f)
    # create mqttclient from json file
    aio_username = data["username"]
    aio_key = data["key"]
    aio_feed_ids = data["feeds"]
    client = MQTTClient(aio_username, aio_key)
    return client, aio_feed_ids

  def connected(self, client):
    logging.info("Connected successfully!")
    [self.client.subscribe(feed_id) for feed_id in self.aio_feed_ids]

  def subscribe(self, client , userdata , mid , granted_qos):
    # print(type(self), type(client))
    logging.info("Subscribed successfully!")
    self.controller.subscribed_feeds += 1

  def disconnected(self, client):
    logging.info("Disconnected from server ...")
    sys.exit(1)

  def message(self, client, feed_id, payload):
    self.controller.process_server_message(feed_id, payload)
  