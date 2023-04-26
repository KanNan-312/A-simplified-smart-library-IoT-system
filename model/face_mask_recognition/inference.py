from deepface.detectors import FaceDetector
import cv2
import pickle
from deepface.commons import distance as dst
from deepface import DeepFace
from deepface.commons import functions
import os
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout
from tensorflow.keras import Model, Input
import numpy as np

# build model
def build_mask_model(input_shape, model='MobileNetV2'):
  base_model = MobileNetV2(input_shape=input_shape, include_top=False, weights='imagenet')
  preprocess_input = tf.keras.applications.mobilenet_v2.preprocess_input

  # freeze the convolutional base
  base_model.trainable = False
  
  # add classification head
  global_average_layer = GlobalAveragePooling2D()
  prediction_layer = Dense(1)

  # Chaining layer
  inputs = Input(shape=input_shape)
  x = preprocess_input(inputs)
  x = base_model(x, training=False)
  x = global_average_layer(x)
  x = Dropout(0.2)(x)
  outputs = prediction_layer(x)
  model = Model(inputs, outputs)

  return model



video = cv2.VideoCapture(0)
model_name = "VGG-Face"
distance_metric = "cosine"
detector_backend =  "opencv"
align = False
detect = False

model = DeepFace.build_model(model_name)
# face_detector = FaceDetector.build_model(detector_backend)
# threshold = dst.findThreshold(model_name, distance_metric)
threshold = 0.25
target_size = functions.find_target_size(model_name=model_name)

# load the pretrained mask classifier
mask_classifier = build_mask_model(input_shape=(224,224,3))
# load checkpoint
check_point_path = "..\..\mask_tracking\\result\\training_1\\cp-0020.ckpt"
mask_classifier.load_weights(check_point_path)

with open("database\\representations_vgg_face.pkl", "rb") as f:
  database = pickle.load(f)

while True:
  ret, frame = video.read()

  if detect:
    detect = False
    face_objs = functions.extract_faces(img=frame, target_size=target_size, \
      detector_backend=detector_backend, grayscale=False, enforce_detection=False, align=True)
  # preprocess objs
  # ...

  # no object found
    if len(face_objs) == 0:
      print("No object")

    else:
      for img, region, confidence in face_objs:
        # represent embedding
        embedding = model.predict(img)[0].tolist()
        matches = []
        matched_distances = []
        for record in database:
          # print(record[0])
          filename = record[0]
          classname = filename.split('/')[-2]
          embed = record[1]
          distance = dst.findCosineDistance(embedding, embed)
          if distance <= threshold:
            matches.append(classname)
            matched_distances.append(distance)

        print(matches)
        print(matched_distances)
        if matches:
          result = max(set(matches), key=matches.count)
        else:
          result = "other"

        x,y,w,h = region['x'], region['y'], region['w'], region['h']
        face_img = frame[y:y+h, x:x+w]
        face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        face_img = cv2.resize(face_img, (224,224))
        face_img = np.expand_dims(face_img, 0)
        prediction = tf.keras.activations.sigmoid(mask_classifier.predict(face_img))[0]
        print(prediction)
        if prediction >= 0.5:
          result += "_mask"
        else:
          result += "_unmask"
        

        # visualization
        x,y,w,h = region['x'], region['y'], region['w'], region['h']
        xmin, xmax, ymin, ymax = x, x+w, y, y+h
        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (255,255,0), 2)
        frame = cv2.putText(frame, result, (xmin, ymin), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255),\
          2, cv2.LINE_AA)
        cv2.imwrite("test_img.jpg", frame)

  cv2.imshow("FaceID", frame)
  if cv2.waitKey(1) == ord('q'):
    detect = True
      
       
      


  # cv2.imshow("ha", frame)
  # if cv2.waitKey(1) == ord('q'):
  #   break

video.release()
cv2.destroyAllWindows()
