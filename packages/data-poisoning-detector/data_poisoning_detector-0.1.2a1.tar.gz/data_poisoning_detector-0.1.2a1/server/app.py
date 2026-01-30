# app_adaptive.py - API with adaptive thresholds
import os
import io
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
import torch
import torch.nn as nn
import joblib
from flask import Flask, Response, request, jsonify
from flask_cors import CORS

import requests as req
from ucimlrepo import fetch_ucirepo
from poison_detector.model import load_model
from poison_detector import poison, detection, preprocess
# from semantic_poisoning import semantic_poison_dataframe

LAST_DATASET = {}
PLAYGROUND_DATASET = {}


def apply_multiple_poisons(X, poison_types, frac, seed=42):
    """
    Sequentially apply multiple poison functions on NumPy array.
    Returns poisoned X and union of poisoned indices.
    """
    rng = np.random.default_rng(seed)
    poisoned_union = set()
    X_curr = X

    for i, ptype in enumerate(poison_types):
        poison_fn = PLAYGROUND_POISON_METHODS[ptype]

        X_curr, idx = poison_fn(
            X_curr,
            frac=frac,
            seed=seed + i
        )

        poisoned_union.update(map(int, idx))

    return X_curr, np.array(sorted(poisoned_union), dtype=int)



PLAYGROUND_POISON_METHODS = {
    "feature_perturb": poison.poison_feature_perturb,
    "representation_inversion": poison.poison_representation_inversion,
    "backdoor": poison.poison_backdoor,
    "clean_label": poison.poison_clean_label,
    "distribution_shift": poison.poison_distribution_shift,
    "outlier_injection": poison.poison_outlier_injection,
    "near_duplicate": poison.poison_near_duplicate,
    "feature_dropout": poison.poison_feature_dropout,
}

# ----------------------------
# Flask setup
# ----------------------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

DEVICE = "cpu"
CKPT_PATH = os.environ.get("CKPT_PATH", "../poison_detector/assets/multi_poison_detector_model.pt")
THRESHOLD_PATH = os.environ.get("THRESHOLD_PATH", "../poison_detector/assets/multi_poison_detector_thresholds.pkl")

if not os.path.exists(CKPT_PATH):
    raise FileNotFoundError(f"Missing checkpoint: {CKPT_PATH}")

# Load model
ckpt = torch.load(CKPT_PATH, map_location=DEVICE)
extra = ckpt.get("extra", {})

model = load_model(CKPT_PATH, device=DEVICE)

# Load pre-trained projections
state_dict = (
    ckpt["model_state"]
    if "model_state" in ckpt
    else ckpt["state_dict"]
)
projection_keys = set()
for key in state_dict.keys():
    if key.startswith("input_projections."):
        dataset_key = key.split(".")[1]
        projection_keys.add(dataset_key)

for dataset_key in projection_keys:
    weight_key = f"input_projections.{dataset_key}.0.weight"
    if weight_key in state_dict:
        input_dim = state_dict[weight_key].shape[1]
        model._get_or_create_projections(input_dim, dataset_key)

model.load_state_dict(state_dict, strict=True)
model.eval()

# Load thresholds
if not os.path.exists(THRESHOLD_PATH):
    raise FileNotFoundError(f"Missing threshold file: {THRESHOLD_PATH}")

threshold_data = joblib.load(THRESHOLD_PATH)

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

# thresholds
threshold_mgr.per_dataset_thresholds = threshold_data.get("per_dataset", {})
threshold_mgr.global_threshold = threshold_data.get("global", 3.5)

# 🔴 REQUIRED for score_universal
threshold_mgr.latent_centroids = threshold_data["latent_centroids"]
threshold_mgr.latent_cov_inv = threshold_data["latent_cov_inv"]
per_dataset_thresholds = threshold_mgr.per_dataset_thresholds
global_threshold = threshold_mgr.global_threshold

print(
    f"✓ Loaded thresholds: "
    f"{len(threshold_mgr.per_dataset_thresholds)} per-dataset, "
    f"global={threshold_mgr.global_threshold:.4f}"
)


def json_error(msg, code=400, **extra):
    payload = {"error": msg}
    payload.update(extra)
    return jsonify(payload), code


def get_threshold(dataset_key: str = None, tau_override: float = None) -> float:
    """Get appropriate threshold: override > per-dataset > global"""
    if tau_override is not None:
        return float(tau_override)
    
    if dataset_key and dataset_key in per_dataset_thresholds:
        return float(per_dataset_thresholds[dataset_key])
    
    return float(global_threshold)

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


# ----------------------------
# Routes
# ----------------------------
@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "device": DEVICE,
        "mode": "ADAPTIVE (per-dataset + global fallback)",
        "max_input_dim": model.max_input_dim,
        "n_trained_datasets": len(projection_keys),
        "n_per_dataset_thresholds": len(threshold_mgr.per_dataset_thresholds),
        "global_threshold": float(threshold_mgr.global_threshold),
        "trained_datasets": sorted(list(projection_keys))
    })


@app.get("/thresholds")
def get_thresholds():
    """Return all available thresholds"""
    return jsonify({
        "per_dataset": {k: float(v) for k, v in threshold_mgr.per_dataset_thresholds.items()},
        "global": float(threshold_mgr.global_threshold)
    })


@app.post("/analyze_csv")
def analyze_csv():
    if "file" not in request.files:
        return json_error("Missing file field 'file'")

    f = request.files["file"]
    print(f"Received file: {f.filename}")
    try:
        df = pd.read_csv(f)
    except Exception as e:
        return json_error("Failed to read CSV", details=str(e))

    dataset_id = f"csv_{hash((f.filename, len(df)))}"
    LAST_DATASET[dataset_id] = {
        "df": df.copy(),
        "poisoned_df": None,
        "poisoned_mask": None,
    }

    tau_override = request.form.get("tau")
    tau_override = float(tau_override) if tau_override else None
    dataset_hint = request.form.get("dataset_hint", "").strip()

    try:
        X_np, _ = preprocess.universal_preprocess(df, max_dim=model.max_input_dim)
    except Exception as e:
        return json_error("Preprocessing failed", code=422, details=str(e))

    upload_key = f"upload_{abs(hash(f.filename))}"
    
    # Score
    preprocess.ensure_latent_stats(threshold_mgr, model, X_np, key=upload_key)
    scores = detection.score_universal(model, X_np, key=upload_key, threshold_mgr=threshold_mgr)
    tau_local = None
    tau_global = global_threshold
    # ----------------------------
    # Adaptive threshold selection
    # ----------------------------
    if tau_override is not None:
        tau = float(tau_override)
        threshold_source = "override"
    elif dataset_hint and dataset_hint in per_dataset_thresholds:
        tau = float(per_dataset_thresholds[dataset_hint])
        threshold_source = "per_dataset"
    else:
        tau, info = get_adaptive_local_threshold(
            scores, global_threshold
        )
        threshold_source = info["mode"]
        tau_local = info["tau_local"]
        tau_global = info["tau_global"]

    flags = (scores >= tau).astype(int)
    print("CSV rows read:", len(df))
    print(df.head(10))
    return jsonify({
        "dataset_id": dataset_id,
        "mode": "adaptive",
        "tau": float(tau),
        "tau_local": float(tau_local) if tau_local is not None else None,
        "tau_global": float(tau_global),
        "threshold_source": threshold_source,
        "n_rows": int(len(scores)),
        "n_features": int(X_np.shape[1]),
        "scores": scores.tolist(),
        "flags": flags.tolist(),
        "flagged_count": int(flags.sum()),
    })


@app.post("/analyze_uci")
def analyze_uci():
    """
    Universal UCI analysis with adaptive threshold
    
    JSON: { "uci_id": 350, "tau": optional }
    """    
    data = request.get_json(force=True)
    uci_id = int(data.get("uci_id", 350))
    
    tau_override = data.get("tau")
    tau_override = float(tau_override) if tau_override else None
    
    try:
        ds = fetch_ucirepo(id=uci_id)
        df = pd.DataFrame(ds.data.features)
    except Exception as e:
        return json_error("Failed to fetch UCI dataset/Dataset not available as an import, please download and use as csv.", details=str(e))
    
    try:
        X_np, preprocessor = preprocess.universal_preprocess(df, max_dim=model.max_input_dim)
    except Exception as e:
        return json_error("Preprocessing failed", code=422, details=str(e))
    
    key = f"uci_{uci_id}_d{X_np.shape[1]}"
    preprocess.ensure_latent_stats(threshold_mgr, model, X_np, key)
    scores = detection.score_universal(model, X_np, key=key, threshold_mgr=threshold_mgr)
    dataset_id = f"uci_{uci_id}"
    LAST_DATASET[dataset_id] = {
        "df": df.copy(),
        "poisoned_df": None,
        "poisoned_mask": None,
    }
    
    # ✅ Initialize defaults
    tau_local = None
    tau_global = global_threshold
    
    # Get adaptive threshold (check if this UCI dataset has a trained threshold)
    if tau_override is not None:
        tau = float(tau_override)
        threshold_source = "override"
    elif key in per_dataset_thresholds:
        tau = float(per_dataset_thresholds[key])
        threshold_source = "per_dataset"
    else:
        tau, info = get_adaptive_local_threshold(
            scores, global_threshold
        )
        threshold_source = info["mode"]
        tau_local = info["tau_local"]
        tau_global = info["tau_global"]

    flags = (scores >= tau).astype(int)
    
    has_trained_projection = key in projection_keys
    
    return jsonify({
        "dataset_id": dataset_id,
        "mode": "adaptive",
        "uci_id": uci_id,
        "tau": float(tau),
        "tau_local": float(tau_local) if tau_local is not None else None,
        "tau_global": float(tau_global),
        "threshold_source": threshold_source,
        "has_trained_projection": has_trained_projection,
        "n_rows": int(X_np.shape[0]),
        "n_features": int(X_np.shape[1]),
        "scores": scores.tolist(),
        "flags": flags.tolist(),
        "flagged_count": int(flags.sum())
    })


@app.post("/analyze_url")
def analyze_url():
    """
    Universal URL analysis with adaptive threshold
    
    JSON: { "url": "https://.../file.csv", "tau": optional, "dataset_hint": optional }
    """
    data = request.get_json(force=True)
    url = str(data.get("url", ""))

    if not url:
        return json_error("Missing 'url' parameter")
    dataset_id = f"url_{hash((url, len(df)))}"
    LAST_DATASET[dataset_id] = {
        "df": df.copy(),
        "poisoned_df": None,
        "poisoned_mask": None,
    }
    data = request.get_json(force=True)
    url = str(data.get("url", ""))

    if not url:
        return json_error("Missing 'url' parameter")
    tau_override = data.get("tau")
    tau_override = float(tau_override) if tau_override else None
    dataset_hint = data.get("dataset_hint", "").strip()
    
    if not url:
        return json_error("Missing 'url' parameter")
    
    try:
        r = req.get(url, timeout=25)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
    except Exception as e:
        return json_error("Failed to fetch CSV from URL", details=str(e))
    
    try:
        X_np, preprocessor = preprocess.universal_preprocess(df, max_dim=model.max_input_dim)
    except Exception as e:
        return json_error("Preprocessing failed", code=422, details=str(e))
    
    key = f"url_{hash(url)}"
    preprocess.ensure_latent_stats(threshold_mgr, model, X_np, key)
    scores = detection.score_universal(model, X_np, key=key, threshold_mgr=threshold_mgr)
    
    if tau_override is not None:
        tau = float(tau_override)
        threshold_source = "override"

    elif dataset_hint and dataset_hint in per_dataset_thresholds:
        tau = float(per_dataset_thresholds[dataset_hint])
        threshold_source = "per_dataset"

    else:
        tau, info = get_adaptive_local_threshold(
            scores, global_threshold
        )
        threshold_source = info["mode"]
        tau_local = info["tau_local"]
        tau_global = info["tau_global"]

    flags = (scores >= tau).astype(int)
    
    return jsonify({
        "dataset_id": dataset_id,
        "mode": "adaptive",
        "url": url,
        "tau": float(tau),
        "tau_local": float(tau_local),
        "tau_global": float(tau_global),
        "threshold_source": threshold_source,
        "n_rows": int(X_np.shape[0]),
        "n_features": int(X_np.shape[1]),
        "scores": scores.tolist(),
        "flags": flags.tolist(),
        "flagged_count": int(flags.sum())
    })


# @app.route("/playground/poison", methods=["POST", "OPTIONS"])
# def playground_poison():
#     # ----------------------------
#     # Preflight (CORS)
#     # ----------------------------
#     if request.method == "OPTIONS":
#         return "", 204

#     data = request.get_json(force=True)

#     dataset_id = data.get("dataset_id")
#     poison_type = data.get("poison_type")          # single
#     poison_types = data.get("poison_types")        # multiple
#     frac = float(data.get("fraction", 0.1))

#     # ----------------------------
#     # Validation
#     # ----------------------------
#     if not dataset_id or dataset_id not in LAST_DATASET:
#         return json_error("Invalid or missing dataset_id")

#     if poison_types:
#         if not isinstance(poison_types, list) or len(poison_types) == 0:
#             return json_error("poison_types must be a non-empty list")

#         for pt in poison_types:
#             if pt not in PLAYGROUND_POISON_METHODS:
#                 return json_error(
#                     f"Unknown poison_type '{pt}'",
#                     available=list(PLAYGROUND_POISON_METHODS.keys())
#                 )
#     else:
#         if poison_type not in PLAYGROUND_POISON_METHODS:
#             return json_error(
#                 f"Unknown poison_type '{poison_type}'",
#                 available=list(PLAYGROUND_POISON_METHODS.keys())
#             )

#     # ----------------------------
#     # Load dataset
#     # ----------------------------
#     store = LAST_DATASET[dataset_id]
#     df = store["df"].copy()

#     # ----------------------------
#     # Preprocess → NumPy (MATCH TRAINING)
#     # ----------------------------
#     X_np, _ = universal_preprocess(df, max_dim=model.max_input_dim)

#     # ----------------------------
#     # Apply poisoning (NUMPY ONLY)
#     # ----------------------------
#     poisoned_union = set()
#     X_curr = X_np

#     if poison_types:
#         # 🔥 MULTI-POISON MODE
#         for i, pt in enumerate(poison_types):
#             poison_fn = PLAYGROUND_POISON_METHODS[pt]

#             X_curr, idx = poison_fn(
#                 X_curr,
#                 frac=frac,
#                 seed=42 + i
#             )

#             poisoned_union.update(map(int, idx))

#         poison_label = "+".join(poison_types)

#     else:
#         # 🔹 SINGLE POISON MODE
#         poison_fn = PLAYGROUND_POISON_METHODS[poison_type]

#         X_curr, idx = poison_fn(
#             X_curr,
#             frac=frac,
#             seed=42
#         )

#         poisoned_union.update(map(int, idx))
#         poison_label = poison_type

#     poisoned_idx = np.array(sorted(poisoned_union), dtype=int)

#     # ----------------------------
#     # Reconstruct DataFrame (SAFE)
#     # ----------------------------
#     poisoned_df = df.copy()
#     poisoned_df["_poisoned"] = 0
#     poisoned_df.loc[
#         poisoned_idx[poisoned_idx < len(poisoned_df)],
#         "_poisoned"
#     ] = 1

#     # ----------------------------
#     # Score poisoned dataset
#     # ----------------------------
#     key = f"playground_{dataset_id}_{poison_label}"

#     preprocess.ensure_latent_stats(threshold_mgr, model, X_np, key)
#     scores = detection.score_universal(
#         model,
#         X_curr,
#         key=key,
#         threshold_mgr=threshold_mgr
#     )

#     tau, info = get_adaptive_local_threshold(
#         scores,
#         global_threshold
#     )
#     threshold_source = info["mode"]
#     tau_local = info["tau_local"]
#     tau_global = info["tau_global"] 
#     flags = (scores >= tau).astype(int)

#     # ----------------------------
#     # Store results
#     # ----------------------------
#     store["poisoned_df"] = poisoned_df
#     store["poisoned_mask"] = flags.tolist()
#     store["poisoned_rows"] = poisoned_idx.tolist()
#     store["poison_label"] = poison_label

#     # ----------------------------
#     # Response
#     # ----------------------------
#     return jsonify({
#         "dataset_id": dataset_id,
#         "poison_type": poison_label,
#         "poison_types": poison_types,
#         "fraction": frac,
#         "tau": float(tau),
#         "tau_local": float(tau_local),
#         "tau_global": float(tau_global),
#         "threshold_source": threshold_source,
#         "n_rows": int(len(scores)),
#         "poisoned_count": int(len(poisoned_idx)),
#         "detected_count": int(flags.sum()),
#         "poisoned_indices": poisoned_idx[:200].tolist(),
#         "scores": scores.tolist(),
#         "flags": flags.tolist(),
#     })



# @app.post("/export_poisoned")
# def export_poisoned():
#     data = request.get_json(force=True)
#     dataset_id = data.get("dataset_id")

#     if dataset_id not in LAST_DATASET:
#         return json_error("Dataset not found")

#     poisoned_df = LAST_DATASET[dataset_id].get("poisoned_df")

#     if poisoned_df is None:
#         return json_error("No poisoned dataset available")

#     return Response(
#         poisoned_df.to_csv(index=False),
#         mimetype="text/csv",
#         headers={"Content-Disposition": "attachment; filename=poisoned_dataset.csv"}
#     )

@app.post("/export_poisoned_excel")
def export_poisoned_excel():
    data = request.get_json(force=True)
    dataset_id = data.get("dataset_id")

    store = LAST_DATASET.get(dataset_id)
    if not store or store["poisoned_df"] is None:
        return json_error("No poisoned dataset available")

    df = store["poisoned_df"]
    poisoned_cells = store.get("poisoned_cells", set())

    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")
    df.to_excel(writer, index=False, sheet_name="Poisoned")

    workbook = writer.book
    worksheet = writer.sheets["Poisoned"]

    highlight = workbook.add_format({
        "bg_color": "#FF6B6B",
        "font_color": "#000000"
    })

    n_rows, n_cols = df.shape

    for (row, col) in poisoned_cells:
        if row >= n_rows or col not in df.columns:
            continue

        excel_row = int(row) + 1  # +1 header
        excel_col = df.columns.get_loc(col)

        worksheet.write(
            excel_row,
            excel_col,
            df.iat[row, excel_col],
            highlight
        )

    writer.close()
    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition":
            "attachment; filename=poisoned_highlighted.xlsx"
        }
    )



@app.post("/export_clean")
def export_clean():
    data = request.get_json(force=True)
    dataset_id = data.get("dataset_id")
    clean_ids = data.get("clean_ids")

    if dataset_id not in LAST_DATASET:
        return json_error("Dataset not found")

    if not isinstance(clean_ids, list) or len(clean_ids) == 0:
        return json_error("No clean_ids provided")

    df = LAST_DATASET[dataset_id]["df"]

    # 🔑 Keep only clean rows
    clean_df = df.iloc[clean_ids].copy()

    return Response(
        clean_df.to_csv(index=False),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=clean_dataset.csv"
        }
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)