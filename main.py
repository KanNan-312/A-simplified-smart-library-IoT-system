from controller import GatewayController
from model import FaceMaskRecognizer, GatewayModel
from view import Dashboard

import argparse
import sys

adafruit_json_key = "adafruit_key.json"

# face mask detection config
faceid_model = "VGG-Face"
face_detector = "opencv"
distance_metric = "cosine"
faceid_database = "model\\face_mask_recognition\\database\\representations_vgg_face.pkl"
mask_classifier_ckpt = "mask_tracking\\result\\training_1\\cp-0020.ckpt"

# frequecies
ai_freq = 120 # the number of iterations between two AI inferences
sensor_freq = 30
status_freq = 20
sleep = 1 # number of seconds between two sensor data readings.
resend = 2
timeout = 10

# last will
will = "This is my last will message from gateway"


def main():
  try:
    # Init the app, mqtt model and face mask recognizer model
    app = Dashboard()
    model = GatewayModel(adafruit_json_key)
    face_mask_recognizer = FaceMaskRecognizer(faceid_model, face_detector, distance_metric, faceid_database, \
       mask_classifier_ckpt)

    # run the controller
    controller = GatewayController(app, model, face_mask_recognizer, ai_freq, sensor_freq, status_freq, \
      sleep, will, resend, timeout)
    controller.start()
    app.run()
  except KeyboardInterrupt:
    sys.exit(1)

if __name__ == '__main__':
  main()