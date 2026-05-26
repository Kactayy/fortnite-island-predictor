import gc
import numpy as np
import pandas as pd
import joblib

from PIL import Image
from embed_images import embed_image
from embed_text import embed_text


# ============================================
# CONFIG
# ============================================

MODEL_PATH = "models/fortnite_predictor.pkl"

INPUT_CSV = "input/sample_islands.csv"

OUTPUT_CSV = "output/predictions.csv"

def embed_image_path(image_path):

    image = Image.open(image_path).convert("RGB")

    return embed_image(image)

# ============================================
# LOAD MODEL

# ============================================

bundle = joblib.load(MODEL_PATH)

model = bundle["model"]
feature_cols = bundle["features"]


# ============================================
# LOAD INPUTS
# ============================================

df = pd.read_csv(INPUT_CSV)

predictions = []


# ============================================
# PROCESS
# ============================================

for i, row in df.iterrows():

    try:

        title = str(row.get("title_t0", ""))
        description = str(row.get("description_t0", ""))
        image_path = str(row.get("image_t0", ""))

        print(f"\n[{i}] Processing")

        # ====================================
        # EMBED IMAGE
        # ====================================

        print("Embedding image...")

        img_vec = embed_image_path(image_path)

        # ====================================
        # EMBED TEXT
        # ====================================

        print("Embedding text...")

        combined_text = f"{title}. {description}"

        txt_vec = embed_text(combined_text)

        # ====================================
        # CREATE FEATURE ROW
        # ====================================

        features = {}

        # image embeddings
        for j, v in enumerate(img_vec):
            features[f"img_{j}"] = float(v)

        # text embeddings
        for j, v in enumerate(txt_vec):
            features[f"dim_{j}"] = float(v)

        # tags
        for col in df.columns:

            if col.startswith("tag_"):
                features[col] = int(row[col])

        # ====================================
        # CREATE DF
        # ====================================

        sample = pd.DataFrame([features])

        # add missing columns
        for col in feature_cols:

            if col not in sample:
                sample[col] = 0

        sample = sample[feature_cols]

        # ====================================
        # PREDICT
        # ====================================

        pred_log = model.predict(sample)[0]

        print(f"PREDICTED LOG: {pred_log}")

        pred = np.expm1(pred_log)

        print(f"PREDICTED PLAYERS: {pred:,.0f}")

        predictions.append({
            "title": title,
            "prediction": pred
        })

        gc.collect()

    except Exception as e:

        print(f"FAILED ROW {i}: {e}")


# ============================================
# SAVE
# ============================================

out_df = pd.DataFrame(predictions)

out_df.to_csv(
    OUTPUT_CSV,
    index=False
)

print(f"\nSaved predictions to {OUTPUT_CSV}")