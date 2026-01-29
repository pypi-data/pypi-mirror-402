#poison.py

import numpy as np
import pandas as pd
import hashlib
from sklearn.neighbors import NearestNeighbors

def _column_groups(X):
    if not isinstance(X, pd.DataFrame):
        return None
    return {
        "numeric": X.select_dtypes(include="number").columns,
        "categorical": X.select_dtypes(include=["object", "category"]).columns,
        "datetime": X.select_dtypes(include=["datetime"]).columns,
        "text": X.select_dtypes(include="string").columns,
    }

def hash_rows(X: np.ndarray):
    return np.array([hashlib.md5(row.tobytes()).hexdigest() for row in X])

def find_duplicates(X: np.ndarray):
    hashes = hash_rows(X)
    counts = pd.Series(hashes).value_counts()
    duplicate_mask = np.isin(hashes, counts[counts > 1].index)
    return duplicate_mask.astype(int)

def knn_density_score(z, k=5):
    nbrs = NearestNeighbors(n_neighbors=k+1).fit(z)
    dists, _ = nbrs.kneighbors(z) #indices
    return dists[:, 1:].mean(axis=1)

def poison_feature_perturb(X, frac=0.05, strength=4.0, features_frac=0.2, seed=42):
    rng = np.random.default_rng(seed)

    # === NUMPY PATH (unchanged) ===
    if isinstance(X, np.ndarray):
        Xp = X.copy()
        n, d = Xp.shape
        k = max(1, int(frac * n))
        poison_idx = rng.choice(n, k, replace=False)

        feat_k = max(1, int(features_frac * d))
        feat_idx = rng.choice(d, feat_k, replace=False)
        sign = rng.choice([-1.0, 1.0], size=(k, feat_k))

        Xp[np.ix_(poison_idx, feat_idx)] += strength * sign
        return Xp, poison_idx

    # === DATAFRAME PATH ===
    Xp = X.copy()
    n = len(Xp)
    k = max(1, int(frac * n))
    poison_idx = rng.choice(n, k, replace=False)
    groups = _column_groups(Xp)

    # numeric
    for c in groups["numeric"]:
        Xp.loc[poison_idx, c] += strength * rng.choice([-1, 1], size=k)

    # categorical
    for c in groups["categorical"]:
        vals = Xp[c].dropna().unique()
        if len(vals) > 1:
            Xp.loc[poison_idx, c] = rng.choice(vals, size=k)

    # text
    for c in groups["text"]:
        Xp.loc[poison_idx, c] = Xp.loc[poison_idx, c].astype(str) + " subtle"

    return Xp, poison_idx

def poison_representation_inversion(X, frac=0.1, seed=42):
    rng = np.random.default_rng(seed)

    if isinstance(X, np.ndarray):
        Xp = X.copy()
        k = int(frac * len(X))
        idx = rng.choice(len(X), k, replace=False)
        Xp[idx] *= -1
        return Xp, idx

    Xp = X.copy()
    k = int(frac * len(Xp))
    idx = rng.choice(len(Xp), k, replace=False)
    groups = _column_groups(Xp)

    # numeric: sign flip
    for c in groups["numeric"]:
        Xp.loc[idx, c] *= -1

    # categorical: swap dominant category
    for c in groups["categorical"]:
        vals = Xp[c].value_counts().index
        if len(vals) > 1:
            Xp.loc[idx, c] = vals[-1]

    # text: polarity flip marker
    for c in groups["text"]:
        Xp.loc[idx, c] = "NOT " + Xp.loc[idx, c].astype(str)

    return Xp, idx

def poison_backdoor(X, frac=0.05, trigger_value=10.0, trigger_features=3, seed=42):
    rng = np.random.default_rng(seed)

    # =========================
    # NUMPY PATH (FIXED)
    # =========================
    if isinstance(X, np.ndarray):
        Xp = X.copy()
        n, d = Xp.shape

        # Guard: too small to poison meaningfully
        if n < 2 or d < 1:
            return Xp, np.array([], dtype=int)

        k = max(1, int(frac * n))

        # Guard: cannot sample n or more without replacement
        if k >= n:
            return Xp, np.array([], dtype=int)

        tf = min(trigger_features, d)

        idx = rng.choice(n, k, replace=False)
        feat_idx = rng.choice(d, tf, replace=False)

        Xp[np.ix_(idx, feat_idx)] += trigger_value
        return Xp, idx

    # =========================
    # DATAFRAME PATH (UNCHANGED)
    # =========================
    Xp = X.copy()
    n = len(Xp)
    k = max(1, int(frac * n))

    if k >= n:
        return Xp, np.array([], dtype=int)

    idx = rng.choice(n, k, replace=False)
    groups = _column_groups(Xp)

    # numeric trigger
    for c in groups["numeric"][:trigger_features]:
        Xp.loc[idx, c] += trigger_value

    # categorical trigger
    for c in groups["categorical"][:1]:
        Xp.loc[idx, c] = "__TRIGGER__"

    # text trigger
    for c in groups["text"][:1]:
        Xp.loc[idx, c] = Xp.loc[idx, c].astype(str) + " cf_update"

    return Xp, idx



def poison_clean_label(X, frac=0.05, epsilon=0.2, seed=42):
    rng = np.random.default_rng(seed)

    if isinstance(X, np.ndarray):
        Xp = X.copy()
        idx = rng.choice(len(X), int(frac * len(X)), replace=False)
        Xp[idx] += rng.normal(0, epsilon, size=Xp[idx].shape)
        return Xp, idx

    Xp = X.copy()
    idx = rng.choice(len(Xp), int(frac * len(Xp)), replace=False)
    groups = _column_groups(Xp)

    for c in groups["numeric"]:
        Xp.loc[idx, c] += rng.normal(0, epsilon, size=len(idx))

    for c in groups["categorical"]:
        Xp.loc[idx, c] = Xp.loc[idx, c]  # unchanged label-consistent

    for c in groups["text"]:
        Xp.loc[idx, c] = Xp.loc[idx, c].astype(str) + "."

    return Xp, idx


def poison_exact_duplicates_raw(df, frac=0.1, seed=42):
    rng = np.random.default_rng(seed)
    n = len(df)
    k = int(frac * n)

    dup_idx = rng.choice(n, k, replace=False)
    df_dup = df.iloc[dup_idx].copy()

    df_poisoned = pd.concat([df, df_dup], ignore_index=True)

    y_true = np.zeros(len(df_poisoned), dtype=int)
    y_true[len(df):] = 1   # duplicated rows

    return df_poisoned, y_true


def poison_sample_duplication(X, frac=0.1, seed=42):
    rng = np.random.default_rng(seed)
    n = len(X)
    k = int(frac * n)
    
    # Randomly duplicate rows
    dup_idx = rng.choice(n, k, replace=False)
    Xp = np.vstack([X, X[dup_idx]])
    
    # Compute hash-based duplicates
    y_labels = find_duplicates(Xp)
    return Xp, np.where(y_labels == 1)[0]

def poison_near_duplicate(X, frac=0.1, noise_std=0.08, feature_frac=0.6, seed=42):
    rng = np.random.default_rng(seed)
    n, d = X.shape
    k = max(1, int(frac * n))

    dup_idx = rng.choice(n, k, replace=False)
    X_dup = X[dup_idx].copy()

    feat_k = max(1, int(feature_frac * d))
    for i in range(k):
        feats = rng.choice(d, feat_k, replace=False)

        # correlated perturbation
        X_dup[i, feats] += (
            0.3 * X_dup[i, feats] +
            rng.normal(0, noise_std, size=len(feats))
        )

    Xp = np.vstack([X, X_dup])

    y = np.zeros(len(Xp), dtype=int)
    y[len(X):] = 1

    return Xp, np.where(y == 1)[0]



def poison_distribution_shift(X, frac=0.3, scale=2.0, seed=42):
    rng = np.random.default_rng(seed)

    if isinstance(X, np.ndarray):
        Xp = X.copy()
        idx = rng.choice(len(X), int(frac * len(X)), replace=False)
        Xp[idx] *= scale
        return Xp, idx

    Xp = X.copy()
    idx = rng.choice(len(Xp), int(frac * len(Xp)), replace=False)
    groups = _column_groups(Xp)

    for c in groups["numeric"]:
        Xp.loc[idx, c] *= scale

    for c in groups["categorical"]:
        Xp.loc[idx, c] = Xp[c].mode()[0]

    for c in groups["datetime"]:
        Xp.loc[idx, c] += pd.to_timedelta("30D")

    return Xp, idx



def poison_outlier_injection(X, frac=0.05, seed=42):
    rng = np.random.default_rng(seed)

    if isinstance(X, np.ndarray):
        Xp = X.copy()
        idx = rng.choice(len(X), int(frac * len(X)), replace=False)
        Xp[idx] *= 10
        return Xp, idx

    Xp = X.copy()
    idx = rng.choice(len(Xp), int(frac * len(Xp)), replace=False)
    groups = _column_groups(Xp)

    for c in groups["numeric"]:
        q3 = Xp[c].quantile(0.75)
        iqr = q3 - Xp[c].quantile(0.25)
        Xp.loc[idx, c] = q3 + 6 * iqr

    for c in groups["categorical"]:
        Xp.loc[idx, c] = "__OUTLIER__"

    return Xp, idx

def poison_feature_dropout(X, frac=0.1, drop_frac=0.3, seed=42):
    rng = np.random.default_rng(seed)

    # ---------- NUMPY PATH ----------
    if isinstance(X, np.ndarray):
        Xp = X.copy()
        idx = rng.choice(len(Xp), max(1, int(frac * len(Xp))), replace=False)

        feat_k = max(1, int(drop_frac * Xp.shape[1]))
        for i in idx:
            feats = rng.choice(Xp.shape[1], feat_k, replace=False)
            Xp[i, feats] = 0.0

        return Xp, idx

    # ---------- DATAFRAME PATH ----------
    Xp = X.copy()
    idx = rng.choice(len(Xp), max(1, int(frac * len(Xp))), replace=False)
    groups = _column_groups(Xp)

    # numeric → NaN
    for c in groups["numeric"]:
        drop_n = max(1, int(drop_frac * len(groups["numeric"])))
        cols = rng.choice(groups["numeric"], drop_n, replace=False)
        Xp.loc[idx, cols] = np.nan

    # categorical → explicit missing token
    for c in groups["categorical"]:
        if rng.random() < drop_frac:
            Xp.loc[idx, c] = "missing"

    # datetime → NaT
    for c in groups["datetime"]:
        if rng.random() < drop_frac:
            Xp.loc[idx, c] = pd.NaT

    # text → empty marker
    for c in groups["text"]:
        if rng.random() < drop_frac:
            Xp.loc[idx, c] = ""

    return Xp, idx


POISON_METHODS = {
    "feature_perturb": poison_feature_perturb,
    "representation_inversion": poison_representation_inversion,
    "backdoor": poison_backdoor,
    "clean_label": poison_clean_label,
    "distribution_shift": poison_distribution_shift,
    "outlier_injection": poison_outlier_injection,
    "near_duplicate": poison_near_duplicate,
    "feature_dropout": poison_feature_dropout,
}