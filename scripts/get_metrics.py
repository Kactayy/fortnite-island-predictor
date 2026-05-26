import json
import time
import random
from pathlib import Path

import requests

# ============================================
# CONFIG
# ============================================

ISLANDS_FILE = Path("data/islands.json")

OUTPUT_DIR = Path("data/metrics")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FAILED_FILE = Path("data/failed_metrics.json")

BASE_URL = "https://api.fortnite.com/ecosystem/v1"

INTERVAL = "day"
REQUEST_DELAY_MIN = 0.2
REQUEST_DELAY_MAX = 0.4

# ============================================
# SESSION
# ============================================

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json"
})

# ============================================
# HELPERS
# ============================================

def load_islands():
    with open(ISLANDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_metrics_url(island_code):
    """
    Example:
    /islands/{code}/metrics/day
    """

    return (
        f"{BASE_URL}/islands/"
        f"{island_code}/metrics/{INTERVAL}"
    )


def fetch_metrics(island_code):

    url = build_metrics_url(island_code)

    response = session.get(url, timeout=30)

    response.raise_for_status()

    return response.json()


def extract_latest_metric(metric_array, field="value"):
    """
    Get most recent NON-NULL metric value.
    """

    if not metric_array:
        return None

    # iterate newest -> oldest
    for item in reversed(metric_array):

        value = item.get(field)

        if value is not None:
            return value

    return None

def extract_latest_retention(retention_array, field="value"):

    if not retention_array:
        return None

    for item in reversed(retention_array):

        value = item.get(field)

        if value is not None:
            return value

    return None


def process_metrics(raw):

    retention = raw.get("retention", [])

    d1 = None
    d7 = None

    if retention:
        d1 = extract_latest_retention(retention, "d1")
        d7 = extract_latest_retention(retention, "d7")

    processed = {
        "averageMinutesPerPlayer":
            extract_latest_metric(
                raw.get("averageMinutesPerPlayer")
            ),

        "peakCCU":
            extract_latest_metric(
                raw.get("peakCCU")
            ),

        "favorites":
            extract_latest_metric(
                raw.get("favorites")
            ),

        "minutesPlayed":
            extract_latest_metric(
                raw.get("minutesPlayed")
            ),

        "recommendations":
            extract_latest_metric(
                raw.get("recommendations")
            ),

        "plays":
            extract_latest_metric(
                raw.get("plays")
            ),

        "uniquePlayers":
            extract_latest_metric(
                raw.get("uniquePlayers")
            ),

        "retention_d1": d1,
        "retention_d7": d7
    }

    return processed


# ============================================
# MAIN
# ============================================

def collect_metrics():

    islands = load_islands()

    failed = []

    total = len(islands)

    for i, island in enumerate(islands, start=1):
        if i > 10:
            break

        island_code = island.get("code")

        if not island_code:
            continue

        out_file = OUTPUT_DIR / f"{island_code}.json"

        # Skip existing
        if out_file.exists():
            print(f"[{i}/{total}] EXISTS: {island_code}")
            continue

        try:

            raw_metrics = fetch_metrics(island_code)

            print(f"[{i}/{total}] RAW METRICS: {raw_metrics}")

            processed_metrics = process_metrics(raw_metrics)

            final_data = {
                "code": island_code,
                "title": island.get("title"),
                "creatorCode": island.get("creatorCode"),
                "category": island.get("category"),
                "tags": island.get("tags", []),
                "metrics": processed_metrics
            }

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(final_data, f, indent=2)

            print(
                f"[{i}/{total}] SAVED: "
                f"{island_code} | "
                f"UP={processed_metrics['uniquePlayers']}"
            )

        except Exception as e:

            print(
                f"[{i}/{total}] FAILED: "
                f"{island_code} | {e}"
            )

            failed.append({
                "code": island_code,
                "reason": str(e)
            })

        time.sleep(
            random.uniform(
                REQUEST_DELAY_MIN,
                REQUEST_DELAY_MAX
            )
        )

    return failed


# ============================================
# SAVE FAILURES
# ============================================

def save_failures(failed):

    with open(FAILED_FILE, "w", encoding="utf-8") as f:
        json.dump(failed, f, indent=2)

    print(f"\nSaved failures to: {FAILED_FILE}")


# ============================================
# ENTRY
# ============================================

if __name__ == "__main__":

    failed = collect_metrics()

    save_failures(failed)

    print("\nDone.")