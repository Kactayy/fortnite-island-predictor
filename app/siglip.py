import torch
from transformers import AutoModel, AutoProcessor

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print("Loading SigLIP...")

MODEL = AutoModel.from_pretrained(
    "google/siglip-base-patch16-224"
).to(DEVICE)

PROCESSOR = AutoProcessor.from_pretrained(
    "google/siglip-base-patch16-224"
)

print("SigLIP loaded")