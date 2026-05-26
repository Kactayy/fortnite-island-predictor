import pandas as pd

# ============================================
# LOAD
# ============================================

base = pd.read_csv("data/ml_dataset.csv")
img = pd.read_csv("data/image_embeddings.csv")
txt = pd.read_csv("data/text_embeddings.csv")

# ============================================
# MERGE
# ============================================

merged = base.merge(img, on="code", how="inner")
merged = merged.merge(txt, on="code", how="inner")

print(f"merged columns: {merged.columns}")

# ============================================
# CLEAN (IMPORTANT STEP)
# ============================================
merged["target"] = merged["max_unique_players_30d"]

drop_cols = [
    "title_t0",
    "description_t0",
    "image_url",
    "creatorCode",
    "category",
    "tags",
    "avg_unique_players_30d",
    "max_unique_players_30d",
    "days_tracked",
    "day1_players",
    "day3_players",
    "day7_players",
    "first_week_avg",
    "growth_day1_to_day7",
]

merged = merged.drop(columns=drop_cols, errors="ignore")

# ============================================
# TARGET
# ============================================


# ============================================
# FINAL FEATURE CLEANUP
# ============================================

# remove ID + target from features
feature_cols = merged.columns.difference(["code", "target"])

X = merged[feature_cols]
y = merged["target"]

# ensure numeric only
X = X.apply(pd.to_numeric, errors="coerce").fillna(0)

final = pd.concat([merged[["code"]], X, y], axis=1)

# ============================================
# SAVE
# ============================================

final.to_csv("data/final_training_dataset.csv", index=False)

print("Saved final_training_dataset.csv")