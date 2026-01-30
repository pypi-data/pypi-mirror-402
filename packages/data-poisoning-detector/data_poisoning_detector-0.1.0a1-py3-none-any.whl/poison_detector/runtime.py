# poison_detector/runtime.py
import joblib
from importlib.resources import files

from poison_detector.model import load_model
from poison_detector.threshold import threshold_mgr

_DEVICE = "cpu"


def init_backend(device=_DEVICE):
    assets = files("poison_detector.assets")

    ckpt_path = assets / "multi_poison_detector_model.pt"
    threshold_path = assets / "multi_poison_detector_thresholds.pkl"

    if not ckpt_path.exists():
        raise FileNotFoundError(f"Missing model checkpoint: {ckpt_path}")

    if not threshold_path.exists():
        raise FileNotFoundError(f"Missing threshold file: {threshold_path}")

    model = load_model(str(ckpt_path), device=device)

    data = joblib.load(threshold_path)
    threshold_mgr.per_dataset_thresholds = data.get("per_dataset", {})
    threshold_mgr.global_threshold = data.get("global", 3.5)
    threshold_mgr.latent_centroids = data["latent_centroids"]
    threshold_mgr.latent_cov_inv = data["latent_cov_inv"]

    return model
