# Fortnite Island Predictor

Estimate how many peak concurrent players a Fortnite Creative island might reach, based on its **listing metadata** — title, description, thumbnail, tags, and a few other Discover-page details.

The project has two parts:

1. **Web app** (`app/`) — fill in your island details and get an instant prediction with explanations.
2. **Data & training pipeline** (`scripts/`) — scrape island data, build a dataset, train the model, and run batch predictions from CSV.

The model combines **SigLIP** image embeddings, **sentence-transformer** text embeddings, and **XGBoost** regression, with **SHAP** values to explain which factors pushed the estimate up or down.

---

## Quick start (web app)

These steps assume you just cloned the repo and want to run predictions in the browser.

### Prerequisites

- **Python 3.10+** (3.11 or 3.12 recommended)
- **~4 GB free disk space** for Python packages and the SigLIP model download
- **GPU optional** — CUDA speeds up embedding; CPU works but the first prediction is slower
- **Git** — you already have the repo if you're reading this

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/FortniteMapAI.git
cd FortniteMapAI
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** This installs PyTorch, transformers, and other ML libraries. The install can take several minutes.

### 4. Start the server

Run from the **project root** (the folder that contains `app/` and `models/`):

```bash
uvicorn app.main:app --reload
```

You should see output like:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 5. Open the app

Go to **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

On the **first prediction**, the app downloads the SigLIP model from Hugging Face (~400 MB) and loads the trained predictor. This can take 1–3 minutes on CPU. Later predictions are faster.

---

## Using the web app

### What to enter

| Field | Required | Notes |
|-------|----------|-------|
| **Title** | Yes | 3–120 characters. Use the exact title from your Discover listing. |
| **Description** | Yes | 10–2,000 characters. Combined with the title for text analysis. |
| **Tags** | No | Comma-separated Fortnite Creative tags, e.g. `gun game, pvp, free for all`. Must match official tag names (case-insensitive). |
| **Promotional video** | No | Checkbox — enable if your listing includes a video trailer. |
| **Additional gallery images** | No | Slider from 0–3. Screenshots beyond the main thumbnail. |
| **Thumbnail** | Yes | JPEG, PNG, WebP, or GIF, max 5 MB. Upload the same image shown on Discover. |

### Tips for accurate results

- Copy **title and description verbatim** from your live listing.
- Use the **same thumbnail** players see on Discover — the model analyzes visual content.
- Tags only help if they match [Fortnite Creative tags](https://create.fortnite.com/) exactly (e.g. `tycoon`, `boxfight`, `team deathmatch`).
- Results are **estimates** based on historical island data. Real performance depends on updates, trends, promotion, and player taste.

### Understanding the results

After you submit, the results section shows:

- **Estimated peak concurrent players** — the model's main prediction.
- **Percentile rank** — where your island sits vs. the training dataset (e.g. "top 15%").
- **Thumbnail / text / metadata impact** — how much each input category influenced the prediction (SHAP magnitude).
- **Dataset comparison** — your estimate vs. average, median, 75th, and 90th percentile islands.
- **Top factors** — human-readable features (tags, video flag, gallery count, etc.) that helped or hurt the estimate. Positive values push the prediction up; negative values pull it down.

---

## API

The web UI posts to `POST /predict` as `multipart/form-data`. You can call it from scripts or other tools.

**Fields:** `title`, `description`, `tags`, `has_video` (0 or 1), `num_extra_images` (0–3), `thumbnail` (file)

**Success (200):**

```json
{
  "prediction": 12500.0,
  "thumbnail_score": 0.42,
  "text_score": 0.38,
  "metadata_score": 0.15,
  "comparison": {
    "mean": 8200.0,
    "median": 5100.0,
    "p75": 9800.0,
    "p90": 18500.0,
    "vs_mean": 1.52,
    "vs_median": 2.45,
    "percentile": 78
  },
  "top_factors": [
    { "feature": "tag_gun game", "impact": 0.12 },
    { "feature": "has_video", "impact": -0.05 }
  ]
}
```

**Validation error (422):**

```json
{
  "errors": {
    "title": "Title must be at least 3 characters.",
    "thumbnail": "Thumbnail image is required."
  }
}
```

---

## Project structure

```
FortniteMapAI/
├── app/                    # Web application
│   ├── main.py             # FastAPI routes
│   ├── predictor.py        # Prediction + SHAP explanations
│   ├── validation.py       # Input validation rules
│   ├── embed_images.py     # SigLIP image embeddings
│   ├── embed_text.py       # Text embeddings
│   ├── siglip.py           # SigLIP model loader
│   ├── tags.py             # Valid Fortnite Creative tag list
│   ├── templates/          # HTML templates
│   └── static/             # CSS and JavaScript
├── models/
│   └── fortnite_predictor.pkl   # Trained XGBoost model + SHAP explainer
├── scripts/                # Data pipeline and CLI tools
├── input/                  # Sample CSVs and test images
├── output/                 # Batch prediction output
└── requirements.txt
```

The `data/` and `cache/` folders are gitignored — they are created when you run the training pipeline locally.

---

## CLI alternatives

### Batch predictions from CSV

```bash
python scripts/predict_island.py
```

Reads `input/sample_islands.csv` by default and writes results to `output/predictions.csv`. See the script for column format (`title_t0`, `description_t0`, `image_t0`, tag columns, etc.).

### Interactive single-island input

```bash
python scripts/add_input.py
```

Prompts you for island details and appends a row to the sample CSV.

---

## Training pipeline (advanced)

To rebuild the model from scratch you need scraped island data (not included in the repo — `data/` is gitignored). The full pipeline is:

```bash
python scripts/run_pipeline.py
```

This runs, in order:

1. `get_islands.py` — scrape island metadata
2. `build_ml_dataset.py` — build ML-ready dataset
3. `embed_images.py` — SigLIP image embeddings
4. `embed_text.py` — text embeddings
5. `merge_embeddings.py` — combine features
6. `train_model.py` — train XGBoost and save `models/fortnite_predictor.pkl`

Individual scripts can also be run on their own. Expect long runtimes and significant disk usage for large datasets.

---

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| `ModuleNotFoundError` | Activate the venv and run `pip install -r requirements.txt` from the project root. |
| Server won't start | Run `uvicorn` from the project root, not from inside `app/`. |
| First prediction hangs | Normal on first run — SigLIP is downloading/loading. Watch the terminal for progress. |
| `models/fortnite_predictor.pkl` missing | The file should be in the repo. If absent, run the training pipeline or restore from a release. |
| Out of memory | Close other apps; use CPU if GPU VRAM is too small; avoid very large thumbnail files. |
| Unknown tag errors | Tags must match Fortnite Creative names exactly, comma-separated, e.g. `pvp`, not `PvP Mode`. |
| PowerShell won't activate venv | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again. |

---

## How it works (brief)

1. **Thumbnail** → SigLIP (`google/siglip-base-patch16-224`) produces a visual embedding.
2. **Title + description** → sentence-transformer produces a text embedding.
3. **Tags, video flag, gallery count** → binary/numeric metadata features.
4. All features are fed into an **XGBoost** regressor trained on historical island peak player counts.
5. A **SHAP TreeExplainer** breaks down which features moved the prediction up or down.

The target variable is peak concurrent players (log-transformed during training). Global dataset statistics (mean, median, percentiles) are bundled in the model file for comparison in the UI.

---

## License

See [LICENSE.md](LICENSE.md).
