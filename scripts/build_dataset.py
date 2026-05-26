import json
from pathlib import Path

import pandas as pd

# ============================================
# CONFIG
# ============================================

METRICS_DIR = Path("data/metrics")

OUTPUT_DIR = Path("data/datasets")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = OUTPUT_DIR / "fortnite_dataset.csv"

# ============================================
# HELPERS
# ============================================

def load_metric_files():

    files = list(METRICS_DIR.glob("*.json"))

    print(f"Found {len(files)} metric files")

    return files


def flatten_tags(tags):
    """
    Convert tag list into a single string.
    """

    if not tags:
        return ""

    return "|".join(tags)


def safe_get(metrics, key):

    value = metrics.get(key)

    if value is None:
        return 0

    return value


# ============================================
# BUILD ROW
# ============================================

def build_row(data):

    metrics = data.get("metrics", {})

    row = {

        # =========================
        # IDENTIFIERS
        # =========================

        "code":
            data.get("code"),

        "title":
            data.get("title", ""),

        "creatorCode":
            data.get("creatorCode", ""),

        "category":
            data.get("category", ""),

        "tags":
            flatten_tags(data.get("tags", [])),


        # =========================
        # TARGET
        # =========================

        # THIS IS YOUR MAIN LABEL
        "uniquePlayers":
            safe_get(metrics, "uniquePlayers"),


        # =========================
        # AUXILIARY METRICS
        # =========================

        "plays":
            safe_get(metrics, "plays"),

        "peakCCU":
            safe_get(metrics, "peakCCU"),

        "minutesPlayed":
            safe_get(metrics, "minutesPlayed"),

        "averageMinutesPerPlayer":
            safe_get(metrics, "averageMinutesPerPlayer"),

        "favorites":
            safe_get(metrics, "favorites"),

        "recommendations":
            safe_get(metrics, "recommendations"),

        "retention_d1":
            safe_get(metrics, "retention_d1"),

        "retention_d7":
            safe_get(metrics, "retention_d7"),


        # =========================
        # ENGINEERED FEATURES
        # =========================

        # clicks → engagement estimate
        "favoritesPerPlayer":
            (
                safe_get(metrics, "favorites")
                / max(
                    safe_get(metrics, "uniquePlayers"),
                    1
                )
            ),

        "recommendationsPerPlayer":
            (
                safe_get(metrics, "recommendations")
                / max(
                    safe_get(metrics, "uniquePlayers"),
                    1
                )
            ),

        "minutesPerPlayer":
            (
                safe_get(metrics, "minutesPlayed")
                / max(
                    safe_get(metrics, "uniquePlayers"),
                    1
                )
            ),

        "ccuPerPlayer":
            (
                safe_get(metrics, "peakCCU")
                / max(
                    safe_get(metrics, "uniquePlayers"),
                    1
                )
            ),

        "playsPerPlayer":
            (
                safe_get(metrics, "plays")
                / max(
                    safe_get(metrics, "uniquePlayers"),
                    1
                )
            )
    }

    return row


# ============================================
# MAIN
# ============================================

def build_dataset():

    files = load_metric_files()

    rows = []

    for i, file in enumerate(files, start=1):
        if i > 10:
            break

        try:

            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            row = build_row(data)

            rows.append(row)

            print(
                f"[{i}/{len(files)}] "
                f"Processed: {row['code']}"
            )

        except Exception as e:

            print(
                f"[{i}/{len(files)}] "
                f"FAILED: {file.name} | {e}"
            )

    # ========================================
    # CREATE DATAFRAME
    # ========================================

    df = pd.DataFrame(rows)

    # ========================================
    # CLEANING
    # ========================================

    # Remove duplicates
    df = df.drop_duplicates(subset=["code"])

    # Remove empty titles
    df = df[df["title"].str.len() > 0]

    # Remove zero-player islands
    df = df[df["uniquePlayers"] > 0]

    # ========================================
    # SORT
    # ========================================

    df = df.sort_values(
        by="uniquePlayers",
        ascending=False
    )

    # ========================================
    # SAVE
    # ========================================

    df.to_csv(OUTPUT_CSV, index=False)

    print("\n====================================")
    print("DATASET COMPLETE")
    print("====================================")
    print(f"Rows: {len(df)}")
    print(f"Saved: {OUTPUT_CSV.resolve()}")

    # ========================================
    # QUICK STATS
    # ========================================

    print("\nTop 10 islands by uniquePlayers:\n")

    print(
        df[
            [
                "title",
                "uniquePlayers",
                "favorites",
                "plays"
            ]
        ].head(10)
    )


# ============================================
# ENTRY
# ============================================

if __name__ == "__main__":

    build_dataset()