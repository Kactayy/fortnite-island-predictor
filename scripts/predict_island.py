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


def estimate_percentile(value, stats):
    thresholds = [
        (95, stats["p95"]),
        (90, stats["p90"]),
        (75, stats["p75"]),
        (50, stats["median"]),
        (0, stats["mean"])
    ]

    for pct, threshold in thresholds:
        if value >= threshold:
            return pct

    return 0

# ============================================
# LOAD MODEL

# ============================================

bundle = joblib.load(MODEL_PATH)

model = bundle["model"]
feature_cols = bundle["features"]
explainer = bundle["explainer"]
global_stats = bundle["global_stats"]


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
        print(f"img_vec hash: {hash(img_vec.tobytes())}")
        print(f"txt_vec hash: {hash(txt_vec.tobytes())}")

        # add missing columns
        for col in feature_cols:

            if col not in sample:
                sample[col] = 0

        sample = sample[feature_cols]

        shap_values = explainer.shap_values(sample)
        sample_shap = shap_values[0]

        contributions = []

        for feature, value in zip(feature_cols, sample_shap):

            contributions.append(
                (feature, float(value))
            )

        contributions.sort(
            key=lambda x: abs(x[1]),
            reverse=True
        )

        # ====================================
        # PREDICT
        # ====================================

        pred_log = model.predict(sample)[0]

        print(f"PREDICTED LOG: {pred_log}")

        pred = np.expm1(pred_log)

        print(f"PREDICTED PLAYERS: {pred:,.0f}")


        human_contributions = [
            x for x in contributions
            if not (
                x[0].startswith("dim_")
                or
                x[0].startswith("img_")
                # or
                # x[0].startswith("text_")
            )
        ]

        print("\nTop factors:")

        for feature, impact in human_contributions[:10]:

            sign = "+" if impact > 0 else ""

            print(
                f"{feature:<40} {sign}{impact:.3f}"
            )

        image_total = np.abs(
            sample_shap[
                sample_shap.feature.str.startswith("img_")
            ]["shap"]
        ).sum()

        text_total = np.abs(
            sample_shap[
                sample_shap.feature.str.startswith("dim_")
            ]["shap"]
        ).sum()

        metadata_total = np.abs(
            sample_shap[
                ~sample_shap.feature.str.startswith("img_")
                & ~sample_shap.feature.str.startswith("dim_")
            ]["shap"]
        ).sum()

        print("\nContribution Summary")

        print(f"Thumbnail : {image_total:+.3f}")
        print(f"Text      : {text_total:+.3f}")
        print(f"Metadata  : {metadata_total:+.3f}")

        mean = global_stats["mean"]
        median = global_stats["median"]
        p75 = global_stats["p75"]
        p90 = global_stats["p90"]
        p95 = global_stats["p95"]

        vs_mean = pred / mean
        vs_median = pred / median

        percentile = estimate_percentile(pred, global_stats)

        print("\nDataset Comparison: ")

        print(f"Average island:   {mean:,.0f}")
        print(f"Median island:    {median:,.0f}")
        print(f"75th percentile:   {p75:,.0f}")
        print(f"90th percentile:   {p90:,.0f}")

        print("\nRelative Performance:")

        print(f"vs average:  {vs_mean:.2f}x")
        print(f"vs median:   {vs_median:.2f}x")

        print(f"\nEstimated percentile: Top {100 - percentile}%")

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