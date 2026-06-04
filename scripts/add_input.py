import os
import pandas as pd
from pathlib import Path

CSV_PATH = "input/sample_islands.csv"

# ==========================================
# LOAD CSV STRUCTURE
# ==========================================

if not Path(CSV_PATH).exists():
    raise FileNotFoundError(
        f"CSV not found: {CSV_PATH}"
    )

df = pd.read_csv(CSV_PATH)

TAG_COLUMNS = [
    c for c in df.columns
    if c.startswith("tag_")
]

# ------------------------------------------
# Normalize:
# "Word Games"
# "word games"
# "WORD GAMES"
# -> tag_word games
# ------------------------------------------

TAG_LOOKUP = {
    col[4:].strip().lower(): col
    for col in TAG_COLUMNS
}


# ==========================================
# HELPERS
# ==========================================

def ask_nonempty(prompt):

    while True:

        value = input(prompt).strip()

        if value:
            return value

        print("Value cannot be empty.")


def ask_int(prompt, minimum=0, maximum=None):

    while True:

        value = input(prompt).strip()

        try:

            value = int(value)

            if value < minimum:
                raise ValueError()

            if maximum is not None and value > maximum:
                raise ValueError()

            return value

        except Exception:

            if maximum is None:
                print(
                    f"Enter a whole number >= {minimum}"
                )
            else:
                print(
                    f"Enter a whole number between "
                    f"{minimum} and {maximum}"
                )


def ask_yes_no(prompt):

    while True:

        value = input(prompt).strip().lower()

        if value in ["y", "yes", "1"]:
            return 1

        if value in ["n", "no", "0"]:
            return 0

        print("Enter yes/no")


# ==========================================
# USER INPUT
# ==========================================

print("\n=== Add Island ===\n")

title = ask_nonempty(
    "Title: "
)

description = ask_nonempty(
    "Description: "
)

# ------------------------------------------
# Thumbnail validation
# ------------------------------------------

while True:

    thumbnail = input(
        "Thumbnail image path: "
    ).strip()

    thumbnail = thumbnail.strip('"').strip("'")

    if not thumbnail:
        print("Thumbnail path required.")
        continue

    if not Path(thumbnail).exists():

        print(
            "Warning: file does not exist."
        )

        confirm = input(
            "Use anyway? (y/n): "
        ).strip().lower()

        if confirm not in ["y", "yes"]:
            continue

    break

# ------------------------------------------
# Optional category
# ------------------------------------------

category = input(
    "Category (optional): "
).strip()

# ------------------------------------------
# Media
# ------------------------------------------

has_video = ask_yes_no(
    "Has video? (yes/no): "
)

num_extra_images = ask_int(
    "Number of extra images: ",
    minimum=0,
    maximum=50
)

# ------------------------------------------
# Tags
# ------------------------------------------

print(
    "\nEnter up to 4 tags."
)
print(
    "Example: Gun Game, PVP, Free For All, Solo"
)

raw_tags = input(
    "Tags: "
).strip()

tags = []

if raw_tags:

    seen = set()

    for tag in raw_tags.split(","):

        tag = tag.strip().lower()

        if not tag:
            continue

        if tag in seen:
            continue

        seen.add(tag)

        tags.append(tag)

    tags = tags[:4]

unknown_tags = []

# ==========================================
# BUILD ROW
# ==========================================

row = {}

for col in df.columns:

    if col.startswith("tag_"):
        row[col] = 0

    else:
        row[col] = ""

# ------------------------------------------
# Core fields
# ------------------------------------------

if "title_t0" in row:
    row["title_t0"] = title

if "description_t0" in row:
    row["description_t0"] = description

if "image_t0" in row:
    row["image_t0"] = thumbnail

if "category" in row:
    row["category"] = category

if "has_video" in row:
    row["has_video"] = has_video

if "num_extra_images" in row:
    row["num_extra_images"] = num_extra_images

# ------------------------------------------
# Tags
# ------------------------------------------

for tag in tags:

    col = TAG_LOOKUP.get(tag)

    if col:
        row[col] = 1
    else:
        unknown_tags.append(tag)

# ==========================================
# REVIEW
# ==========================================

print("\n========================")
print("ISLAND PREVIEW")
print("========================")

print(f"Title: {title}")
print(f"Description: {description[:150]}")

if len(description) > 150:
    print("...")

print(f"Thumbnail: {thumbnail}")
print(f"Category: {category}")
print(f"Has Video: {has_video}")
print(f"Extra Images: {num_extra_images}")

selected_tags = [
    t for t in tags
    if t not in unknown_tags
]

print(
    f"Tags: {', '.join(selected_tags) or 'None'}"
)

if unknown_tags:

    print(
        "\nUnknown tags ignored:"
    )

    for tag in unknown_tags:
        print(f"  - {tag}")

confirm = input(
    "\nAdd this row? (y/n): "
).strip().lower()

if confirm not in ["y", "yes"]:

    print("Cancelled.")
    raise SystemExit()

# ==========================================
# APPEND
# ==========================================

df = pd.concat(
    [df, pd.DataFrame([row])],
    ignore_index=True
)

df.to_csv(
    CSV_PATH,
    index=False
)

print(
    f"\nAdded island to {CSV_PATH}"
)