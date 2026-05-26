import numpy as np
import pandas as pd
import torch
import joblib

from PIL import Image
from embed_images import embed_image
from embed_text import embed_text


# ============================================
# CONFIG
# ============================================

MODEL_PATH = "models/fortnite_predictor.pkl"

IMAGE_PATH = "input/test_thumbnail.jpeg"

TITLE = "STEAL THE BRAINROT"

DESCRIPTION = """
Hey
game
"""

# ============================================
# LOAD TRAINED MODEL
# ============================================

bundle = joblib.load(MODEL_PATH)

model = bundle["model"]
feature_cols = bundle["features"]



def embed_image_path(image_path):

    image = Image.open(image_path).convert("RGB")

    return embed_image(image)


print("Embedding image...")
img_vec = embed_image_path(IMAGE_PATH)

print("Embedding text...")
text = f"{TITLE}. {DESCRIPTION}"
txt_vec = embed_text(text)


# ============================================
# CREATE ROW
# ============================================

row = {}

# image features
for i, v in enumerate(img_vec):
    row[f"img_{i}"] = float(v)

# text features
for i, v in enumerate(txt_vec):
    row[f"text_{i}"] = float(v)


# ============================================
# CREATE DATAFRAME
# ============================================

sample = pd.DataFrame([row])


# add missing cols
for col in feature_cols:

    if col not in sample:
        sample[col] = 0


# ensure same column order
sample = sample[feature_cols]


# ============================================
# PREDICT
# ============================================

pred_log = model.predict(sample)[0]

pred = np.expm1(pred_log)

print("\n==========================")
print("PREDICTED UNIQUE PLAYERS")
print("==========================")
print(f"{pred:,.0f}")