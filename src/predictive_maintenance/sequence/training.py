"""Training utilities for neural sequence classifiers."""

from __future__ import annotations

import copy
import random
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from sklearn.metrics import average_precision_score
from torch import nn
from torch.utils.data import DataLoader, Dataset


class WindowDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    def __init__(
        self,
        values: np.ndarray,
        labels: np.ndarray,
        endpoints: np.ndarray,
        window_size: int,
    ) -> None:
        self.values = values
        self.labels = labels.astype(np.float32, copy=False)
        self.endpoints = endpoints.astype(np.int64, copy=False)
        self.window_size = window_size

    def __len__(self) -> int:
        return len(self.endpoints)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        endpoint = int(self.endpoints[index])
        start = endpoint - self.window_size + 1
        window = torch.from_numpy(self.values[start : endpoint + 1])
        label = torch.tensor(self.labels[endpoint])
        return window, label


@dataclass(frozen=True)
class TrainingResult:
    best_epoch: int
    epochs_completed: int
    best_validation_average_precision: float
    duration_seconds: float
    parameter_count: int
    history: tuple[dict[str, float], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "best_epoch": self.best_epoch,
            "epochs_completed": self.epochs_completed,
            "best_validation_average_precision": self.best_validation_average_precision,
            "duration_seconds": self.duration_seconds,
            "parameter_count": self.parameter_count,
            "history": list(self.history),
        }


def set_reproducible_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def predict_probabilities(
    model: nn.Module,
    dataset: Dataset[tuple[torch.Tensor, torch.Tensor]],
    *,
    batch_size: int,
    device: torch.device,
) -> np.ndarray:
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=device.type == "cuda",
    )
    model.eval()
    batches: list[np.ndarray] = []
    with torch.inference_mode():
        for values, _ in loader:
            logits = model(values.to(device, non_blocking=True))
            batches.append(torch.sigmoid(logits).cpu().numpy())
    return np.concatenate(batches) if batches else np.empty(0, dtype=np.float32)


def train_classifier(
    model: nn.Module,
    train_dataset: WindowDataset,
    validation_dataset: WindowDataset,
    *,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    weight_decay: float,
    patience: int,
    device: torch.device,
    seed: int,
) -> TrainingResult:
    set_reproducible_seed(seed)
    model.to(device)
    train_labels = train_dataset.labels[train_dataset.endpoints]
    positives = max(1, int(train_labels.sum()))
    negatives = max(1, len(train_labels) - positives)
    pos_weight = torch.tensor([negatives / positives], device=device)
    loss_function = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=learning_rate, weight_decay=weight_decay
    )
    generator = torch.Generator().manual_seed(seed)
    loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        generator=generator,
        num_workers=0,
        pin_memory=device.type == "cuda",
    )

    best_score = -1.0
    best_epoch = 0
    best_state: dict[str, torch.Tensor] | None = None
    stale_epochs = 0
    history: list[dict[str, float]] = []
    started = time.perf_counter()
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        rows = 0
        for values, labels in loader:
            values = values.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            logits = model(values)
            loss = loss_function(logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += float(loss.detach()) * len(labels)
            rows += len(labels)

        probabilities = predict_probabilities(
            model, validation_dataset, batch_size=batch_size, device=device
        )
        validation_labels = validation_dataset.labels[validation_dataset.endpoints]
        score = float(average_precision_score(validation_labels, probabilities))
        history.append(
            {
                "epoch": float(epoch),
                "train_loss": total_loss / max(1, rows),
                "validation_average_precision": score,
            }
        )
        if score > best_score + 1e-6:
            best_score = score
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            stale_epochs = 0
        else:
            stale_epochs += 1
            if stale_epochs >= patience:
                break

    if best_state is None:
        raise RuntimeError("Training produced no model checkpoint")
    model.load_state_dict(best_state)
    duration = time.perf_counter() - started
    return TrainingResult(
        best_epoch=best_epoch,
        epochs_completed=len(history),
        best_validation_average_precision=best_score,
        duration_seconds=duration,
        parameter_count=sum(parameter.numel() for parameter in model.parameters()),
        history=tuple(history),
    )
