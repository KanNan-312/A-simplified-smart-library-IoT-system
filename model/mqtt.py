from Adafruit_IO import MQTTClient
import json

def create_mqtt_client(json_key):
  with open(json_key, "r") as f:
    data = json.load(f)
  # create mqttclient from json file
  aio_username = data["username"]
  aio_key = data["key"]
  aio_feed_ids = data["feeds"]
  client = MQTTClient(aio_username, aio_key)
  return client, aio_feed_ids