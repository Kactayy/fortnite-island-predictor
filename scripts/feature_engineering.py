import numpy as np


def add_features(df):

    # engagement ratios
    df["favorites_per_play"] = df["favorites_30d"] / (df["plays_30d"] + 1)

    df["ccu_per_play"] = df["ccu_30d"] / (df["plays_30d"] + 1)

    # log scaling
    df["log_plays"] = np.log1p(df["plays_30d"])
    df["log_ccu"] = np.log1p(df["ccu_30d"])

    # virality proxy
    df["engagement_score"] = (
        df["favorites_30d"] +
        df["ccu_30d"] * 2
    )

    return df