import json
import csv
import os
from datetime import datetime, timezone
from pathlib import Path

from extract_initial_state import build_initial_state
# from metrics_window import fetch_metrics, process_metrics
from tags import TAGS


ISLANDS_FILE = "data/islands.json"
OUTPUT_FILE = Path("data/ml_dataset.csv")
CHECKPOINT_FILE = Path("cache/completed_ml_dataset.txt")



def load_completed():

    if not CHECKPOINT_FILE.exists():
        return set()

    with open(CHECKPOINT_FILE, "r") as f:
        return set(x.strip() for x in f.readlines())



def mark_completed(code):

    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(CHECKPOINT_FILE, "a") as f:
        f.write(code + "\n")

def sanitize(value):
    if value is None:
        return ""

    value = str(value)

    # kill real newlines
    value = value.replace("\n", " ")
    value = value.replace("\r", " ")

    # collapse whitespace
    value = " ".join(value.split())

    return value

def append_row(row, write_header=False):
    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)

    file_exists = Path(OUTPUT_FILE).exists()

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=row.keys(),
            quoting=csv.QUOTE_ALL,
            escapechar="\\"
        )

        if write_header or not file_exists:
            writer.writeheader()

        writer.writerow(row)
    # OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:

    #     writer = csv.DictWriter(
    #         f,
    #         fieldnames=row.keys()
    #     )

    #     if write_header:
    #         writer.writeheader()

    #     writer.writerow(row)

def encode_tags(tag_list):
    tag_set = set(tag_list)

    return [
        1 if tag in tag_set else 0
        for tag in TAGS
    ]

# =========================
# LOAD ISLANDS
# =========================

def load_islands_map():

    with open(ISLANDS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {x["code"]: x for x in data}

# =========================
# MAIN PIPELINE
# =========================

def build_dataset():
    islands_map = load_islands_map()

    completed = load_completed()

    first_write = not OUTPUT_FILE.exists()

    for i, (code, island_meta) in enumerate(islands_map.items()):
        if i < 4868:
            continue
        # if i > 1403:
        #     break

        if code in completed:
            print(f"[{i}] SKIP {code}")
            continue

        try:

            print(f"[{i}] PROCESSING {code}")


            initial = build_initial_state(
                code,
                islands_map
            )

            t0_str = initial.get("start_date")

            if t0_str:
                t0 = datetime.fromisoformat(t0_str)
            else:
                t0 = datetime.now(timezone.utc)

            metrics = initial.get("player_metrics")

            if metrics is None:
                print(f"[SKIP] No player metrics found for {code}")
                continue

            avg_players = metrics.get("avg_unique_players_30d")
            max_players = metrics.get("max_unique_players_30d")

            if (
                avg_players is None or
                max_players is None or
                max_players < 20
            ):
                print(f"[SKIP] Insufficient data for {code}")
                continue
                
            tags = island_meta.get("tags", [])
            tag_vector = encode_tags(tags)

            daily = metrics["daily_unique_players"]

            day1_players = daily[0] if len(daily) > 0 else 0
            day3_players = daily[2] if len(daily) > 2 else 0
            day7_players = daily[6] if len(daily) > 6 else 0

            first_week_avg = (
                sum(daily[:7]) / min(len(daily), 7)
            ) if daily else 0

            growth_day1_to_day7 = (
                day7_players / max(day1_players, 1)
            )


            row = {
                "code": sanitize(code),
                "title_t0": sanitize(initial.get("title")),
                "description_t0": sanitize(initial.get("description")),
                "image_t0": sanitize(initial.get("image")),
                "category": sanitize(island_meta.get("category")),
                "creatorCode": sanitize(island_meta.get("creatorCode")),
                "avg_unique_players_30d": metrics.get("avg_unique_players_30d"),
                "max_unique_players_30d": metrics.get("max_unique_players_30d"),
                "has_video": initial.get("has_video"),
                "num_extra_images": initial.get("num_extra_images"),
                "days_tracked": metrics.get("days_tracked"),
                "day1_players": day1_players,
                "day3_players": day3_players,
                "day7_players": day7_players,
                "first_week_avg": first_week_avg,
                "growth_day1_to_day7": growth_day1_to_day7,
            }

            for tag_name, value in zip(TAGS, tag_vector):
                row[f"tag_{tag_name}"] = value

            append_row(
                row,
                write_header=first_write
            )

            first_write = False

            mark_completed(code)

            print(f"[{i}] SAVED {code}")

        except Exception as e:

            print(f"[{i}] FAILED {code}: {e}")


if __name__ == "__main__":
    build_dataset()

