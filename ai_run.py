import socket
from model import FaceMaskRecognizer
import cv2

def run_face_mask_detection(recognizer):
  # Server information
  host = '127.0.0.1'
  port = 12345

  # create socket and connect to server
  s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
  s.connect((host,port))

  # initialize web cam stream
  cap = cv2.VideoCapture(0)

	# message you send to server
  while True:
    try:
      # message sent to server
      ret, frame = cap.read()
      if ret:
        detection_results = recognizer.detect(frame)
        if len(detection_results) > 0:
          res = detection_results[0]
          name = res[0]
          s.send(name.encode('utf-8'))
          print(name)
    except KeyboardInterrupt:
      break
        

  # close the connection
  s.close()
  cap.release()
  cv2.releaseAllWindows()

if __name__ == "__main__":  
  faceid_model = "VGG-Face"
  face_detector = "opencv"
  distance_metric = "cosine"
  faceid_database = "model\\face_mask_recognition\\database\\representations_vgg_face.pkl"
  mask_classifier_ckpt = "mask_tracking\\result\\training_1\\cp-0020.ckpt"

  recognizer = FaceMaskRecognizer(faceid_model, face_detector, distance_metric, faceid_database, mask_classifier_ckpt)
  run_face_mask_detection(recognizer)