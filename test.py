from model import FaceMaskRecognizer
import cv2

faceid_model = "VGG-Face"
face_detector = "opencv"
distance_metric = "cosine"
faceid_database = "model\\face_mask_recognition\\database\\representations_vgg_face.pkl"
mask_classifier_ckpt = "mask_tracking\\result\\training_1\\cp-0020.ckpt"

recognizer = FaceMaskRecognizer(faceid_model, face_detector, distance_metric, faceid_database, mask_classifier_ckpt)

cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
  print(recognizer.detect(frame))