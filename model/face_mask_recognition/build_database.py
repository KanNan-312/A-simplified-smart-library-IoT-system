from deepface import DeepFace
import glob

models = [
  "VGG-Face", 
  "Facenet", 
  "Facenet512", 
  "OpenFace", 
  "DeepFace", 
  "DeepID", 
  "ArcFace", 
  "Dlib",
  "SFace",
]

metrics = ["cosine", "euclidean", "euclidean_l2"]
# VGG
'''
  normalization = "VGGFace"
  targetsize: 224,224
'''
backends = [
  'opencv', 
  'ssd', 
  'dlib', 
  'mtcnn', 
  'retinaface',
  'mediapipe'
]

# result = DeepFace.verify(
#   img1_path = "thanh1.jpg",
#   img2_path = "thanh2.jpg",
#   model_name=models[0],
#   distance_metric=metrics[0],
#   detector_backend = backends[0]
#   )
# print(result)


result = DeepFace.find(
  img_path = "faceid/thanh1.jpg",
  db_path = "faceid/database/",
  model_name="VGG-Face",
  distance_metric="cosine",
  detector_backend = "mtcnn"
  )


# DeepFace.stream(db_path = "database", model_name="DeepFace", distance_metric="cosine", detector_backend = "mtcnn")


# embedding_objs = DeepFace.represent(model_name=models[0], img_path = "thanh1.jpg")