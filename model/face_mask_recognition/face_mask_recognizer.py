from deepface import DeepFace
from deepface.commons import functions, distance as dst
from model import MaskClassifier
import cv2
import pickle
import numpy as np


class FaceMaskRecognizer():
  def __init__(self, faceid_model, face_detector, distance_metric, faceid_database, mask_classifier_ckpt, \
     faceid_thres=0.4):
    self.faceid_model = DeepFace.build_model(faceid_model)
    self.face_detector = face_detector
    self.faceid_thres = faceid_thres
    # load faceid database
    with open(faceid_database, 'rb') as f:
      self.database = pickle.load(f)

    # build mask classifier
    self.mask_classifier = MaskClassifier(mask_classifier_ckpt)
    
  def detect(self, frame):
    face_objs = functions.extract_faces(img=frame, target_size=(224,224), \
      detector_backend=self.face_detector, grayscale=False, enforce_detection=False, align=True)

    if len(face_objs) == 0:
      return []
    else:
      results = []
      for img, region, confidence in face_objs:
        # represent embedding
        embedding = self.faceid_model.predict(img, verbose=0)[0].tolist()
        matches = []
        matched_distances = []
        # loop in faceid database to find matches
        for record in self.database:
          classname = record[0].split('/')[-2]
          embed = record[1]
          distance = dst.findCosineDistance(embedding, embed)
          if distance <= self.faceid_thres:
            matches.append(classname)
          
        if matches:
          person_name = max(set(matches), key=matches.count)
        else:
          person_name = "guest"

        # Detect wearing mask
        x,y,w,h = region['x'], region['y'], region['w'], region['h']
        face_img = frame[y:y+h, x:x+w]
        mask_score = self.mask_classifier.predict_mask(face_img)
        mask = True if mask_score >= 0.5 else False
        
        results.append((person_name, mask))
      
      return results