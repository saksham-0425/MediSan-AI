import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array, load_img
import matplotlib.pyplot as plt
from tf_keras_vis.saliency import Saliency
from tf_keras_vis.utils.model_modifiers import ReplaceToLinear
from tf_keras_vis.utils.scores import CategoricalScore
import cv2

# Load model
model = load_model("model/pneumonia_model.h5")

IMG_SIZE = 150

def get_heatmap(img_path, save_path="gradcam_output.jpg"):
    # Preprocess image
    img = load_img(img_path, target_size=(IMG_SIZE, IMG_SIZE))
    img = img_to_array(img) / 255.0
    img = np.expand_dims(img, axis=0)

    def loss(output):
        return output[:, 0]  # class index 0 for 'pneumonia'

    def model_modifier(m):
        m.layers[-1].activation = tf.keras.activations.linear

    saliency = Saliency(model,
                        model_modifier=model_modifier,
                        clone=True)

    cam = saliency(loss, img)
    cam = np.maximum(cam[0], 0)

    heatmap = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
    heatmap = cv2.resize(heatmap, (IMG_SIZE, IMG_SIZE))
    heatmap = np.uint8(255 * heatmap)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

    # Overlay on image
    orig = cv2.imread(img_path)
    orig = cv2.resize(orig, (IMG_SIZE, IMG_SIZE))
    overlay = cv2.addWeighted(orig, 0.5, heatmap, 0.5, 0)

    # Save
    cv2.imwrite(save_path, overlay)
    print(f"✅ Heatmap saved at: {save_path}")
    return save_path


