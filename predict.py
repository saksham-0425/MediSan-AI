import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
import cv2

# Load model
model = tf.keras.models.load_model("model/pneumonia_model.h5")

def preprocess_image(img_path):
    img = image.load_img(img_path, target_size=(150, 150))
    img_array = image.img_to_array(img)
    img_array = img_array / 255.0  # normalize
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def predict_pneumonia(img_path):
    processed = preprocess_image(img_path)
    prediction = model.predict(processed)[0][0]
    if prediction > 0.5:
        return "PNEUMONIA", float(prediction)
    else:
        return "NORMAL", float(prediction)

if __name__ == "__main__":
    result, confidence = predict_pneumonia("test_images/sample1.jpeg")
    print(f"Prediction: {result} (Confidence: {confidence:.2f})")
