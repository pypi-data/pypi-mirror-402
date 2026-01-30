# poison_detector/detection.py
import numpy as np
import torch
from sklearn.metrics import confusion_matrix
from poison_detector.poison import knn_density_score
from poison_detector import preprocess, threshold
import torch.nn.functional as F

_model = None

def set_model(model):
    global _model
    _model = model

# -------------------------
# Utils
# -------------------------

def mad_normalize(x, eps=1e-9):
    med = np.median(x)
    mad = np.median(np.abs(x - med)) + eps
    return (x - med) / mad


def latent_deviation(z, mu, cov_inv):
    diff = z - mu
    return torch.sqrt(torch.sum(diff @ cov_inv * diff, dim=1))

def analyze_dataframe(df, *, dataset_id=None, dataset_key=None, tau_override=None, type='analyze'):
    X_np, _ = preprocess.universal_preprocess(df, 512)
    key = dataset_key or f"generic_{X_np.shape[1]}"
    preprocess.ensure_latent_stats(threshold.threshold_mgr, _model, X_np, key)
    scores = score_universal(
        _model,
        X_np,
        key=key,
        threshold_mgr=threshold.threshold_mgr
    )
    tau_local = None
    tau_global = threshold.threshold_mgr.global_threshold
    if tau_override is not None:
        tau = float(tau_override)
        threshold_source = "override"
    elif key in threshold.threshold_mgr.per_dataset_thresholds:
        tau = float(threshold.threshold_mgr.per_dataset_thresholds[key])
        threshold_source = "per_dataset"
    else:
        tau, info = threshold.get_adaptive_local_threshold(scores, threshold.threshold_mgr.global_threshold)
        threshold_source = info["mode"]
        tau_local = info["tau_local"]
        tau_global = info["tau_global"]
    flags = (scores >= tau).astype(int)
    clean_df = df.loc[flags == 0].reset_index(drop=True)
    if type == 'analyze':
        return {
            "n_rows": int(X_np.shape[0]),
            "n_features": int(X_np.shape[1]),
            "flagged_count": int(flags.sum()),
            "contamination_rate": int(flags.sum()) / int(X_np.shape[0]) if int(X_np.shape[0]) > 0 else 0,
            "threshold": {
                "tau": float(tau),
                "tau_local": tau_local,
                "tau_global": tau_global,
                "threshold_source": threshold_source,
            }
        }
    elif type == 'clean':
        return clean_df


# -------------------------
# Core scoring (PURE)
# -------------------------
def probe_influence_score(probe, z):
    """
    Per-sample gradient influence score.
    Stable, single backward pass.
    Returns: tensor of shape (N,)
    """
    probe.eval()

    z = z.detach().requires_grad_(True)

    logits = probe(z)
    pseudo_labels = logits.argmax(dim=1)

    # single scalar loss (sum over samples)
    loss = F.cross_entropy(logits, pseudo_labels)

    # gradient of loss w.r.t. representations
    grad = torch.autograd.grad(loss, z, retain_graph=False)[0]

    return grad.norm(dim=1)


@torch.no_grad()
def score_universal(model, X, key="default", threshold_mgr=None):
    model.eval()

    x = torch.tensor(X).float()
    xhat, z = model(x, key=key)

    # --------------------
    # Base anomaly signals
    # --------------------
    recon = ((xhat - x) ** 2).mean(1)

    mu = threshold_mgr.latent_centroids[key]
    cov_inv = threshold_mgr.latent_cov_inv[key]
    latent_dev = latent_deviation(z, mu, cov_inv)

    recon_n = mad_normalize(recon.cpu().numpy())
    latent_n = mad_normalize(latent_dev.cpu().numpy())

    cls_score = torch.softmax(model.classifier(z), dim=1)[:, 1]
    cls_n = mad_normalize(cls_score.cpu().numpy())

    base_score = 0.4 * recon_n + 0.4 * latent_n + 0.2 * cls_n

    # --------------------
    # Density (near-duplicate only)
    # --------------------
    z_np = z.cpu().numpy()
    knn_score = knn_density_score(z_np, k=5)     # small = dense
    knn_n = mad_normalize(knn_score)

    # --------------------
    # GATING (CRITICAL)
    # --------------------
    is_near_duplicate_candidate = (
        (recon_n < np.percentile(recon_n, 40)) &
        (latent_n < np.percentile(latent_n, 40)) &
        (knn_n < np.percentile(knn_n, 20))
    )

    # --------------------
    # Conditional fusion
    # --------------------
    final_score = base_score.copy()
    alpha = 0.6

    final_score[is_near_duplicate_candidate] += (
        alpha * mad_normalize(-knn_score)[is_near_duplicate_candidate]
    )

    with torch.enable_grad():
        influence = probe_influence_score(threshold_mgr.probe, z)

    influence_n = mad_normalize(influence.cpu().numpy())
    influence_n = np.clip(influence_n, -3.0, 3.0)

    # Only apply when sample looks clean
    is_clean_like = (
        (recon_n < np.percentile(recon_n, 40)) &
        (latent_n < np.percentile(latent_n, 40))
    )

    n = len(X)

    use_influence = (
        (n > 1000) & is_clean_like
    )

    final_score[use_influence] += 0.8 * influence_n[use_influence]
    return final_score

# -------------------------
# Evaluation helper
# -------------------------

def eval_metrics(scores, y, tau):
    pred = (scores > tau).astype(int)
    cm = confusion_matrix(y, pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    return {
        "TP": int(tp),
        "FP": int(fp),
        "TN": int(tn),
        "FN": int(fn),
        "Precision": tp / (tp + fp + 1e-9),
        "Recall": tp / (tp + fn + 1e-9),
        "F1": 2 * tp / (2 * tp + fp + fn + 1e-9),
        "FPR": fp / (fp + tn + 1e-9),
        "Accuracy": (tp + tn) / (tp + tn + fp + fn + 1e-9),
    }
