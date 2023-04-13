from controller import GatewayController
from model import MaskDetector, GatewayModel
from view import Dashboard

import argparse
import sys

adafruit_json_key = "adafruit_key.json"

# ai model config
ai_weights = "model/mask_detection/weights/keras_model.h5"
ai_labels = "model/mask_detection/weights/labels.txt"

# frequecies
ai_freq = 5000 # the number of iterations between two AI inferences
sensor_freq = 20
status_freq = 20
sleep = 1 # number of seconds between two sensor data readings.

# last will
will = "This is my last will message"


def main():
  try:
    app = Dashboard()
    model = GatewayModel(adafruit_json_key, ai_weights, ai_labels)
    controller = GatewayController(app, model, ai_freq, sensor_freq, status_freq, sleep, will)
    controller.start()
    app.run()
  except KeyboardInterrupt:
    sys.exit(1)

if __name__ == '__main__':
  main()