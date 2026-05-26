import joblib
import pandas as pd
import numpy as np


MODEL_PATH = "models/fortnite_predictor.pkl"


bundle = joblib.load(MODEL_PATH)

model = bundle["model"]
features = bundle["features"]


# ============================================
# LOAD NEW SAMPLE
# ============================================

sample = pd.read_csv(
    "input/sample.csv"
)

# add missing cols
for col in features:
    if col not in sample:
        sample[col] = 0

sample = sample[features]


# ============================================
# PREDICT
# ============================================

pred_log = model.predict(sample)

pred = np.expm1(pred_log)

print("\nPredicted uniquePlayers:\n")

for p in pred:
    print(f"{p:,.0f}")