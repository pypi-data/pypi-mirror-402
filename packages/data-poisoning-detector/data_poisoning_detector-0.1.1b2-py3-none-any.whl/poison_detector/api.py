import os
import pandas as pd
from ucimlrepo import fetch_ucirepo
from poison_detector import detection
from poison_detector.runtime import init_backend
from poison_detector.detection import set_model
import warnings

MODEL = None

def _ensure_initialized():
    global MODEL
    if MODEL is None:
        MODEL = init_backend(
            ckpt_path="poison_detector/assets/multi_poison_detector_model.pt",
            threshold_path="poison_detector/assets/multi_poison_detector_thresholds.pkl",
        )
        set_model(MODEL)

def analyze_uci(uci_id: int):
    warnings.warn("poison-detector is in BETA. APIs may change/Results may differ", UserWarning)
    _ensure_initialized()
    ds = fetch_ucirepo(id=uci_id)
    df = pd.DataFrame(ds.data.features)

    return detection.analyze_dataframe(
        df,
        dataset_id=f"uci_{uci_id}",
        dataset_key=f"uci_{uci_id}_d{df.shape[1]}",
    )


def analyze_csv(path: str):
    warnings.warn("poison-detector is in BETA. APIs may change.", UserWarning)
    df = pd.read_csv(path)

    return detection.analyze_dataframe(
        df,
        dataset_id=f"csv_{os.path.basename(path)}",
        dataset_key=f"csv_{hash(path)}",
    )


def clean_uci(uci_id: int):

    ds = fetch_ucirepo(id=uci_id)
    df = pd.DataFrame(ds.data.features)

    return detection.analyze_dataframe(
        df,
        dataset_key=f"uci_{uci_id}_d{df.shape[1]}",
        type="clean",
    )