#model.py
import os
import torch

import torch
import torch.nn as nn

class UniversalSSL(nn.Module):
    def __init__(self, latent=64, hidden=256, max_input_dim=512, num_classes=2):
        super().__init__()
        self.max_input_dim = max_input_dim
        self.hidden = hidden
        self.latent = latent

        self.classifier = nn.Linear(latent, num_classes)

        self.encoder = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, latent),
        )

        self.decoder_core = nn.Sequential(
            nn.Linear(latent, hidden),
            nn.ReLU(),
        )

        self.input_projections = nn.ModuleDict()
        self.output_projections = nn.ModuleDict()

    def _get_or_create_projections(self, input_dim: int, key: str):
        if key in self.input_projections:
            proj = self.input_projections[key]
            if proj[0].in_features != input_dim:
                del self.input_projections[key]
                del self.output_projections[key]

        if key not in self.input_projections:
            self.input_projections[key] = nn.Sequential(
                nn.Linear(input_dim, self.hidden),
                nn.ReLU(),
                nn.Linear(self.hidden, self.hidden),
            )
            self.output_projections[key] = nn.Linear(self.hidden, input_dim)

        return self.input_projections[key], self.output_projections[key]

    def encode(self, x, key="default"):
        proj_in, _ = self._get_or_create_projections(x.shape[1], key)
        h = proj_in(x)
        return self.encoder(h)

    def forward(self, x, key="default"):
        proj_in, proj_out = self._get_or_create_projections(x.shape[1], key)
        h = proj_in(x)
        z = self.encoder(h)
        h_dec = self.decoder_core(z)
        x_recon = proj_out(h_dec)
        return x_recon, z
    
def load_model(ckpt_path, device="cpu"):
    ckpt = torch.load(ckpt_path, map_location=device)

    # -----------------------------
    # Detect checkpoint format
    # -----------------------------
    if isinstance(ckpt, dict) and "model_state" in ckpt:
        state = ckpt["model_state"]
        extra = ckpt.get("extra", {})

    elif isinstance(ckpt, dict) and "state_dict" in ckpt:
        state = ckpt["state_dict"]
        extra = ckpt.get("extra", {})

    elif isinstance(ckpt, dict):
        # 🔑 raw state_dict
        state = ckpt
        extra = {}

    else:
        raise ValueError("Unsupported checkpoint format")

    # -----------------------------
    # Build model
    # -----------------------------
    model = UniversalSSL(
        latent=extra.get("latent", 64),
        hidden=extra.get("hidden", 256),
        max_input_dim=extra.get("max_input_dim", 512),
    ).to(device)

    # -----------------------------
    # Restore projections BEFORE loading weights
    # -----------------------------
    projection_keys = {
        k.split(".")[1]
        for k in state
        if k.startswith("input_projections.")
    }

    for key in projection_keys:
        w = f"input_projections.{key}.0.weight"
        if w in state:
            input_dim = state[w].shape[1]
            model._get_or_create_projections(input_dim, key)

    # -----------------------------
    # Load weights
    # -----------------------------
    model.load_state_dict(state, strict=True)
    model.eval()
    return model

