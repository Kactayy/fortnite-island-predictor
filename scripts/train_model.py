# train_model.py

import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    r2_score
)

from xgboost import XGBRegressor


# ============================================
# CONFIG
# ============================================

DATASET_PATH = "data/final_training_dataset.csv"

MODEL_OUTPUT = "models/fortnite_predictor.pkl"

TARGET_COLUMN = "target"


# ============================================
# LOAD DATASET
# ============================================

df = pd.read_csv(DATASET_PATH)

print(f"Loaded {len(df)} rows")


# ============================================
# CLEAN TARGET
# ============================================

df = df[df[TARGET_COLUMN] > 0]

# log-transform target
df["target_log"] = np.log1p(df[TARGET_COLUMN])


# ============================================
# FEATURES
# ============================================

drop_cols = [
    "code",
    "target",
    "target_log"
]

feature_cols = [
    c for c in df.columns
    if c not in drop_cols
]

X = df[feature_cols]
y = df["target_log"]


print(f"Feature count: {len(feature_cols)}")


# ============================================
# TRAIN / TEST SPLIT
# ============================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


# ============================================
# MODEL
# ============================================

model = XGBRegressor(

    # trees
    n_estimators=1200,

    # tree complexity
    max_depth=8,

    # learning rate
    learning_rate=0.03,

    # randomness
    subsample=0.8,
    colsample_bytree=0.8,

    # regularization
    reg_alpha=0.5,
    reg_lambda=1.0,

    # performance
    tree_method="hist",

    random_state=42
)


# ============================================
# TRAIN
# ============================================

print("\nTraining model...\n")

model.fit(
    X_train,
    y_train
)


# ============================================
# EVALUATION
# ============================================

preds_log = model.predict(X_test)

preds = np.expm1(preds_log)
actual = np.expm1(y_test)

mae = mean_absolute_error(actual, preds)
r2 = r2_score(actual, preds)

print("\n==============================")
print("MODEL PERFORMANCE")
print("==============================")

print(f"MAE: {mae:,.2f}")
print(f"R² : {r2:.4f}")

print("\nExample predictions:\n")

for i in range(min(10, len(preds))):

    print(
        f"Predicted: {preds[i]:,.0f} | "
        f"Actual: {actual.iloc[i]:,.0f}"
    )


# ============================================
# SAVE MODEL
# ============================================

joblib.dump(
    {
        "model": model,
        "features": feature_cols
    },
    MODEL_OUTPUT
)

print(f"\nSaved model -> {MODEL_OUTPUT}")