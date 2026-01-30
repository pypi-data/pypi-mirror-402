
from poison_detector import detection
import numpy as np
import joblib
import torch
from typing import Dict, Optional
from sklearn.model_selection import train_test_split
import torch.nn as nn

class BackendThresholdManager:
    """Lightweight threshold manager for inference-only backend"""
    pass

class LinearProbe(nn.Module):
    def __init__(self, z_dim):
        super().__init__()
        self.fc = nn.Linear(z_dim, 2)

    def forward(self, z):
        return self.fc(z)
    
probe = LinearProbe(z_dim=64)

threshold_mgr = BackendThresholdManager()
threshold_mgr.probe = probe

def dataset_regime(X):
    n, d = X.shape
    if n < 500 or d < 3:
        return "small"
    return "normal"

def get_adaptive_local_threshold(scores: np.ndarray, global_tau: float):
    """
    Compute a dataset-specific threshold using contamination-robust calibration,
    with a global lower bound for safety.
    """
    if len(scores) < 20:
        # Too small to estimate safely → fallback
        return float(global_tau), "global_fallback_small_sample"

    # Step 1: select low-risk anchor set (assumed mostly clean)
    anchor_mask = scores <= np.percentile(scores, 70)
    anchor_scores = scores[anchor_mask]

    if len(anchor_scores) < 10:
        return float(global_tau), "global_fallback_insufficient_anchor"

    # Step 2: robust threshold on anchor
    med = np.median(anchor_scores)
    mad = np.median(np.abs(anchor_scores - med)) + 1e-9
    tau_local = med + 3.5 * mad

    # Step 3: enforce global safety bound
    tau_final = max(tau_local, global_tau)

    return float(tau_final), {
        "mode": "adaptive_local+global",
        "tau_local": float(tau_local),
        "tau_global": float(global_tau),
        "tau_final": float(tau_final),
        "anchor_size": int(len(anchor_scores)),
    }

class ThresholdStrategy:
    """Base class for threshold strategies"""
    
    def fit(self, clean_scores: np.ndarray):
        raise NotImplementedError
    
    def get_threshold(self) -> float:
        raise NotImplementedError


class QuantileThreshold(ThresholdStrategy):
    def __init__(self, fpr_cap=0.01):
        self.fpr_cap = fpr_cap
        self.threshold = None
    
    def fit(self, clean_scores: np.ndarray):
        self.threshold = np.quantile(clean_scores, 1 - self.fpr_cap)
        return self
    
    def get_threshold(self) -> float:
        return float(self.threshold)

class ThresholdManager:
    def __init__(self, strategy: str = "quantile", global_fallback: bool = True, **strategy_kwargs):
        self.strategy_name = strategy
        self.strategy_kwargs = strategy_kwargs
        self.global_fallback = global_fallback
        
        self.per_dataset_thresholds = {}
        self.global_threshold = None
        self.global_threshold_obj = None
    
    def _create_strategy(self) -> ThresholdStrategy:
        if self.strategy_name == "quantile":
            return QuantileThreshold(**self.strategy_kwargs)
        # elif self.strategy_name == "mad":
        #     return MADThreshold(**self.strategy_kwargs)
        # elif self.strategy_name == "iqr":
        #     return IQRThreshold(**self.strategy_kwargs)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy_name}")
    
    def fit_per_dataset(self, model, Xtr_dict: Dict[str, np.ndarray], val_frac=0.2):
        """
        Fit per-dataset thresholds and latent statistics for a universal poison detector.

        Args:
            model: The trained model with an `encode` method.
            Xtr_dict: Dict of datasets, key=dataset_name, value=np.ndarray of clean data.
            val_frac: Fraction of data to use for validation.
        """
        print(f"\n=== Fitting Per-Dataset Thresholds ({self.strategy_name}) ===")
        
        all_clean_scores = []
        self.latent_centroids = {}
        self.latent_cov_inv = {}
        self.per_dataset_thresholds = {}

        model.eval()  # Ensure model is in eval mode

        for ds_name, Xtr in Xtr_dict.items():
            X_train, X_val = train_test_split(Xtr, test_size=val_frac, random_state=42)

            with torch.no_grad():
                x_val_tensor = torch.tensor(X_val).float()
                z = model.encode(x_val_tensor, key=ds_name)  # latent encoding

                mu = z.mean(0)
                cov = torch.cov(z.T) + 1e-4 * torch.eye(z.shape[1])

                self.latent_centroids[ds_name] = mu
                self.latent_cov_inv[ds_name] = torch.linalg.inv(cov)

            # Pass self as threshold_mgr so latent stats are accessible
            scores = detection.score_universal(model, X_val, key=ds_name, threshold_mgr=self)
            all_clean_scores.append(scores)

            regime = dataset_regime(Xtr)

            if regime == "small":
                strategy = QuantileThreshold(fpr_cap=0.005)  # 99.5%
            else:
                strategy = self._create_strategy()
            if np.std(scores) < 1e-6 or np.isnan(scores).any():
                print(f"  ⚠️ {ds_name}: degenerate scores → using global threshold")
                self.per_dataset_thresholds[ds_name] = np.nan
            else:
                strategy.fit(scores)
                tau = strategy.get_threshold()
                self.per_dataset_thresholds[ds_name] = tau

            print(f"  {ds_name}: τ = {tau:.4f}")

        if self.global_fallback:
            normalized_scores = [detection.mad_normalize(scores) for scores in all_clean_scores if np.std(scores) > 1e-6]

            if len(normalized_scores) > 0:
                all_scores = np.concatenate(normalized_scores)
                self.global_threshold_obj = self._create_strategy()
                self.global_threshold_obj.fit(all_scores)
                self.global_threshold = self.global_threshold_obj.get_threshold()
            else:
                self.global_threshold = None

            print(f"\n  Global fallback: τ = {self.global_threshold:.4f}")

    
    def get_threshold(self, dataset_key: Optional[str] = None) -> float:
        if dataset_key and dataset_key in self.per_dataset_thresholds:
            return self.per_dataset_thresholds[dataset_key]
        
        if self.global_threshold is not None and not np.isnan(self.global_threshold):
            return self.global_threshold
        
        raise ValueError("No threshold available")
    
    def save(self, path: str):
        joblib.dump({
            "strategy": self.strategy_name,
            "strategy_kwargs": self.strategy_kwargs,
            "per_dataset": self.per_dataset_thresholds,
            "global": self.global_threshold,
            "global_fallback": self.global_fallback,
            "latent_centroids": self.latent_centroids,
            "latent_cov_inv": self.latent_cov_inv
        }, path)
    
    @classmethod
    def load(cls, path: str):
        data = joblib.load(path)
        manager = cls(
            strategy=data["strategy"],
            global_fallback=data["global_fallback"],
            **data["strategy_kwargs"]
        )
        manager.per_dataset_thresholds = data["per_dataset"]
        manager.global_threshold = data["global"]
        return manager