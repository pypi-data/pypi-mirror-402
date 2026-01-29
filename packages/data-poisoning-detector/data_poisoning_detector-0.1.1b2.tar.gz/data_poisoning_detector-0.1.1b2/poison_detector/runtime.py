import os
import torch
import joblib
from poison_detector.model import load_model
from poison_detector.threshold import threshold_mgr

_DEVICE = "cpu"

def init_backend(
    ckpt_path: str,
    threshold_path: str,
):
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"Missing model checkpoint: {ckpt_path}")

    if not os.path.exists(threshold_path):
        raise FileNotFoundError(f"Missing threshold file: {threshold_path}")

    model = load_model(ckpt_path, device=_DEVICE)

    data = joblib.load(threshold_path)
    threshold_mgr.per_dataset_thresholds = data.get("per_dataset", {})
    threshold_mgr.global_threshold = data.get("global", 3.5)
    threshold_mgr.latent_centroids = data["latent_centroids"]
    threshold_mgr.latent_cov_inv = data["latent_cov_inv"]

    return model
