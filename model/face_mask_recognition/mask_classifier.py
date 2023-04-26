import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout
from tensorflow.keras import Model, Input
import cv2
import numpy as np

class MaskClassifier:
  def __init__(self, ckpt, model='MobileNetV2'):
    self.model = self.__build_model(input_shape=(224,224,3))
    self.model.load_weights(ckpt)

  def predict_mask(self, face_img):
    face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
    face_img = cv2.resize(face_img, (224,224))
    face_img = np.expand_dims(face_img, 0)
    mask_score = tf.keras.activations.sigmoid(self.model.predict(face_img, verbose=0))[0]
    return mask_score

  
  def __build_model(self, input_shape, model='MobileNetV2'):
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