import csv
import pandas as pd
import torch
import gc
import os

from dotenv import load_dotenv
from pathlib import Path
from transformers import AutoProcessor, AutoModel

load_dotenv()
INPUT_CSV = "data/ml_dataset.csv"
OUTPUT_CSV = "data/text_embeddings.csv"
CHECKPOINT_FILE = "cache/completed_text.txt"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


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
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    row = [code] + vec.tolist()

    file_exists = os.path.exists(OUTPUT_CSV)

    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        if write_header or not file_exists:
            header = ["code"] + [f"dim_{i}" for i in range(len(vec))]
            writer.writerow(header)

        writer.writerow(row)

    # row = {
    #     "code": code
    # }

    # for i, val in enumerate(vec):
    #     row[f"text_{i}"] = float(val)

    # with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:

    #     writer = csv.DictWriter(
    #         f,
    #         fieldnames=row.keys()
    #     )

    #     if write_header:
    #         writer.writeheader()

# ============================================
# EMBED TEXT
# ============================================


def embed_text(text):

    if not text or str(text).strip() == "":
        text = "fortnite island"

    inputs = processor(
        text=[text],
        return_tensors="pt",
        padding=True,
        truncation=True
    ).to(DEVICE)

    inputs = {
        k: v.to(DEVICE)
        for k, v in inputs.items()
    }

    with torch.no_grad():

        outputs = model.text_model(
            input_ids=inputs["input_ids"]
        )

        pooled = outputs.pooler_output

        pooled = pooled / pooled.norm(
            dim=-1,
            keepdim=True
        )

    vec = pooled[0].cpu().numpy()

    del outputs
    del pooled
    del inputs

    gc.collect()

    if DEVICE == "cuda":
        torch.cuda.empty_cache()

    return vec


# ============================================
# MAIN
# ============================================


df = pd.read_csv(INPUT_CSV)

completed = load_completed()

first_write = not Path(OUTPUT_CSV).exists()

for i, row in df.iterrows():

    code = row["code"]

    if code in completed:
        print(f"[{i}] SKIP {code}")
        continue

    try:

        title = str(row.get("title_t0", ""))
        desc = str(row.get("description_t0", ""))

        text = f"{title}. {desc}"

        vec = embed_text(text)

        print("VECTOR SHAPE:", len(vec))
        print("FIRST VALUE:", vec[0])

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