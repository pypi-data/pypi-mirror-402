
#preprocess.py
from sklearn.compose import ColumnTransformer
from sklearn.discriminant_analysis import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
import torch
import numpy as np

def universal_preprocess(df, max_dim=512):
    df = df.replace([np.inf, -np.inf], np.nan)

    # Optional: clip extreme numeric values
    for col in df.select_dtypes(include=["number"]).columns:
        df[col] = df[col].clip(-1e6, 1e6)

    # Identify numeric vs categorical columns
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = [c for c in df.columns if c not in num_cols]

    # --- FIX: Force categorical columns to string ---
    for c in cat_cols:
        df[c] = df[c].fillna("missing").astype(str)

    transformers = []
    if num_cols:
        transformers.append(("num", Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler())
        ]), num_cols))
    
    if cat_cols:
        transformers.append(("cat", Pipeline([
            ("imp", SimpleImputer(strategy="most_frequent")),
            ("oh", OneHotEncoder(handle_unknown="ignore", sparse_output=False, max_categories=20))
        ]), cat_cols))

    if not transformers:
        raise ValueError("DataFrame has no numeric or categorical columns")

    preprocessor = ColumnTransformer(transformers)
    X = preprocessor.fit_transform(df).astype(np.float32)
    
    if X.shape[1] > max_dim:
        X = X[:, :max_dim]
    
    return X, preprocessor

def ensure_latent_stats(threshold_mgr, model, X, key):
    """
    Ensure latent centroid & covariance exist for a dataset key.
    If missing (unseen dataset), estimate from current data.
    """
    if key in threshold_mgr.latent_centroids:
        return

    with torch.no_grad():
        x = torch.tensor(X).float()
        z = model.encode(x, key=key)

        mu = z.mean(0)
        cov = torch.cov(z.T) + 1e-4 * torch.eye(z.shape[1])

    threshold_mgr.latent_centroids[key] = mu
    threshold_mgr.latent_cov_inv[key] = torch.linalg.inv(cov)

    print(f"[adaptive] Initialized latent stats for unseen dataset: {key}")
    