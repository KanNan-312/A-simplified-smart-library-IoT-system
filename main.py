from controller.gateway_controller import GatewayController
import logging, argparse
import sys

adafruit_json_key = "adafruit_key.json"
sleep = 1 # number of seconds between two sensor data readings.
# ai model config
ai_weights = "model/mask_detection/weights/keras_model.h5"
ai_labels = "model/mask_detection/weights/labels.txt"
ai_skip = 30 # the number of iterations between two AI inferences

def main():
  controller = GatewayController(adafruit_json_key, ai_weights, ai_labels, ai_skip, sleep)
  controller.run()

if __name__ == '__main__':
  main()