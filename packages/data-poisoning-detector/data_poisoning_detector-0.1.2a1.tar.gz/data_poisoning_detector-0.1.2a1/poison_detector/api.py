import os
import pandas as pd
from ucimlrepo import fetch_ucirepo
from urllib.parse import urlparse
from poison_detector import detection
from poison_detector.runtime import init_backend
from poison_detector.detection import set_model
import warnings
from typing import Literal

_MODEL_INITIALIZED = False

def _ensure_initialized():
    global _MODEL_INITIALIZED
    if not _MODEL_INITIALIZED:
        model = init_backend()
        set_model(model)
        _MODEL_INITIALIZED = True

def analyze(source: Literal["uci", "csv", "url"], dataset: int | str):
    warnings.warn("poison-detector is in BETA. APIs may change/Results may differ", UserWarning)
    _ensure_initialized()

    if source == 'csv' and isinstance(dataset, str):
        path = dataset
        try:
            df = pd.read_csv(path)
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {path}")
        
        return detection.analyze_dataframe(
            df,
            dataset_id=f"csv_{os.path.basename(path)}",
            dataset_key=f"csv_{hash(path)}",
        )
    elif source == 'uci' and isinstance(dataset, int):
        uci_id = dataset
        ds = fetch_ucirepo(id=uci_id)
        if(ds is None):
            raise ValueError(f"UCI dataset with id {uci_id} not found or cannot be imported.")
        df = pd.DataFrame(ds.data.features)

        return detection.analyze_dataframe(
            df,
            dataset_id=f"uci_{uci_id}",
            dataset_key=f"uci_{uci_id}_d{df.shape[1]}",
        )
    elif source == 'url' and isinstance(dataset, str):
        url = dataset

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Invalid URL provided.")

        df = pd.read_csv(url)

        filename = os.path.basename(parsed.path) or "remote.csv"

        return detection.analyze_dataframe(
            df,
            dataset_id=f"url_{filename}",
            dataset_key=f"url_{hash(url)}",
        )
    else:
        raise ValueError("Invalid source or dataset type.")

def clean(source: Literal["uci", "csv", "url"], dataset: int | str):
    warnings.warn("poison-detector is in BETA. APIs may change/Results may differ", UserWarning)
    _ensure_initialized()
    if source == 'csv' and isinstance(dataset, str):
        path = dataset
        try:
            df = pd.read_csv(path)
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {path}")

        return detection.analyze_dataframe(
            df,
            dataset_id=f"csv_{os.path.basename(path)}",
            dataset_key=f"csv_{hash(path)}",
            type="clean",
        )

    elif source == 'uci' and isinstance(dataset, int):
        uci_id = dataset
        ds = fetch_ucirepo(id=uci_id)
        if(ds is None):
            raise ValueError(f"UCI dataset with id {uci_id} not found or cannot be imported.")
        df = pd.DataFrame(ds.data.features)

        return detection.analyze_dataframe(
            df,
            dataset_key=f"uci_{uci_id}_d{df.shape[1]}",
            type="clean",
        )
    elif source == 'url' and isinstance(dataset, str):
        url = dataset

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Invalid URL provided.")

        df = pd.read_csv(url)

        filename = os.path.basename(parsed.path) or "remote.csv"

        return detection.analyze_dataframe(
            df,
            dataset_id=f"url_{filename}",
            dataset_key=f"url_{hash(url)}",
        )
    else:
        raise ValueError("Invalid source or dataset type.")