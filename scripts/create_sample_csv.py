import pandas as pd


# ============================================
# HARD CODED ISLANDS
# ============================================

islands = [

    {
        "title_t0": "STEAL THE BRAINROT",
        "description_t0": (
            "Steal brainrots from other players "
            "and become rich"
        ),
        "image_t0": "input/test_thumbnail.jpeg",

        "tag_tycoon": 1,
        "tag_funny": 1,
        "tag_pvp": 0,
        "tag_boxfight": 0
    },

    {
        "title_t0": "RANKED BOXFIGHTS",
        "description_t0": (
            "Competitive realistic boxfight arena"
        ),
        "image_t0": "input/test_thumbnail.jpeg",

        "tag_tycoon": 0,
        "tag_funny": 0,
        "tag_pvp": 1,
        "tag_boxfight": 1
    }
]


# ============================================
# SAVE
# ============================================

df = pd.DataFrame(islands)

df.to_csv(
    "input/sample_islands2.csv",
    index=False
)

print("Saved sample_islands.csv")