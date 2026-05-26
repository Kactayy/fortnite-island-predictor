import subprocess
import sys


STEPS = [
    "get_islands.py",
    "build_ml_dataset.py",
    "embed_images.py",
    "embed_text.py",
    "merge_embeddings.py",
    "train_model.py"
]


for step in STEPS:
    step = "scripts/" + step
    print("\n" + "=" * 60)
    print(f"RUNNING {step}")
    print("=" * 60)

    result = subprocess.run([
        sys.executable,
        step
    ])

    if result.returncode != 0:

        print(f"FAILED: {step}")
        sys.exit(1)


print("\nPIPELINE COMPLETE")