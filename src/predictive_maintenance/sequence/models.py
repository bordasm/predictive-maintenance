"""PyTorch LSTM and Transformer classifiers for fixed temporal windows."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import torch
from torch import nn


class LSTMClassifier(nn.Module):
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 64,
        num_layers: int = 1,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size,
            hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.head = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, 1),
        )

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        encoded, _ = self.lstm(values)
        return self.head(encoded[:, -1]).squeeze(-1)


class TransformerClassifier(nn.Module):
    def __init__(
        self,
        input_size: int,
        window_size: int,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 128,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        if d_model % nhead:
            raise ValueError("d_model must be divisible by nhead")
        self.input_projection = nn.Linear(input_size, d_model)
        self.position = nn.Parameter(torch.empty(1, window_size, d_model))
        nn.init.normal_(self.position, mean=0.0, std=0.02)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
            norm_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(
            layer, num_layers=num_layers, enable_nested_tensor=False
        )
        self.normalization = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, 1)
        self.scale = math.sqrt(d_model)

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        encoded = self.input_projection(values) * self.scale
        encoded = encoded + self.position[:, : values.shape[1]]
        encoded = self.encoder(encoded)
        return self.head(self.normalization(encoded[:, -1])).squeeze(-1)


def build_sequence_model(
    name: str,
    *,
    input_size: int,
    window_size: int,
    parameters: dict[str, Any],
) -> nn.Module:
    if name == "lstm":
        return LSTMClassifier(input_size=input_size, **parameters)
    if name == "transformer":
        return TransformerClassifier(
            input_size=input_size, window_size=window_size, **parameters
        )
    raise ValueError(f"Unsupported sequence model: {name}")


def load_sequence_checkpoint(
    path: str | Path, *, device: str | torch.device = "cpu"
) -> tuple[nn.Module, dict[str, Any]]:
    """Reconstruct an inference-ready model from a governed checkpoint."""
    checkpoint = torch.load(path, map_location=device, weights_only=True)
    model = build_sequence_model(
        checkpoint["model"],
        input_size=int(checkpoint["input_size"]),
        window_size=int(checkpoint["window_size"]),
        parameters=checkpoint["config"],
    )
    model.load_state_dict(checkpoint["state_dict"])
    model.to(device)
    model.eval()
    return model, checkpoint

