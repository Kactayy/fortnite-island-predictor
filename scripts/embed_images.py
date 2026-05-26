import csv
import pandas as pd
import torch
import gc
import requests
from io import BytesIO

from pathlib import Path
from PIL import Image
from transformers import AutoProcessor, AutoModel
from dotenv import load_dotenv

load_dotenv()

INPUT_CSV = "data/ml_dataset.csv"
OUTPUT_CSV = "data/image_embeddings.csv"
CHECKPOINT_FILE = "cache/completed_images.txt"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# ============================================
# MODEL
# ============================================

model = AutoModel.from_pretrained(
    "google/siglip-base-patch16-224",
    token=os.getenv("HF_TOKEN")
).to(DEVICE)

processor = AutoProcessor.from_pretrained(
    "google/siglip-base-patch16-224",
    token=os.getenv("HF_TOKEN")
)

# ============================================
# HELPERS
# ============================================


def load_completed():

    path = Path(CHECKPOINT_FILE)

    if not path.exists():
        return set()

    with open(path, "r") as f:
        return set(x.strip() for x in f.readlines())



def mark_completed(code):

    Path(CHECKPOINT_FILE).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(CHECKPOINT_FILE, "a") as f:
        f.write(code + "\n")

def append_embedding(code, vec, write_header=False):

    row = {
        "code": code
    }

    for i, val in enumerate(vec):
        row[f"img_{i}"] = float(val)

    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=row.keys()
        )

        if write_header:
            writer.writeheader()

        writer.writerow(row)


# ============================================
# EMBED
# ============================================

def embed_image_url(url):

    response = requests.get(url, timeout=20)
    image = Image.open(BytesIO(response.content)).convert("RGB")

    return embed_image(image)


def embed_image(image):

    inputs = processor(images=image, return_tensors="pt").to(DEVICE)
    
    with torch.no_grad():

        features = model.get_image_features(**inputs)

        # FORCE tensor safety
        if not isinstance(features, torch.Tensor):
            features = features.pooler_output

        features = features.float()
        features = features / features.norm(dim=-1, keepdim=True)

    return features[0].cpu().numpy()


# ============================================
# MAIN
# ============================================


df = pd.read_csv(INPUT_CSV)

completed = load_completed()

first_write = not Path(OUTPUT_CSV).exists()

print(f"number of rows: {df}")

for i, row in df.iterrows():

    code = row["code"]

    if code in completed:
        print(f"[{i}] SKIP {code}")
        continue

    image_url = row["image_t0"]

    if not isinstance(image_url, str) or image_url == "":
        print(f"[{i}] SKIP {code} (no image url)")
        continue

    try:

        vec = embed_image_url(image_url)

        append_embedding(
            code,
            vec,
            write_header=first_write
        )

        first_write = False

        mark_completed(code)

        print(f"[{i}] SAVED {code}")

    except Exception as e:

        print(f"[{i}] FAILED {code}: {e}")