from __future__ import annotations

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from predictive_maintenance.sequence.models import (  # noqa: E402
    LSTMClassifier,
    TransformerClassifier,
    load_sequence_checkpoint,
)
from predictive_maintenance.sequence.training import WindowDataset  # noqa: E402


def test_sequence_models_return_one_logit_per_window() -> None:
    values = torch.randn(4, 8, 6)
    lstm = LSTMClassifier(input_size=6, hidden_size=12)
    transformer = TransformerClassifier(
        input_size=6,
        window_size=8,
        d_model=12,
        nhead=3,
        num_layers=1,
        dim_feedforward=24,
    )

    assert lstm(values).shape == (4,)
    assert transformer(values).shape == (4,)


def test_window_dataset_returns_only_history_ending_at_label_row() -> None:
    values = np.arange(30, dtype=np.float32).reshape(10, 3)
    labels = np.arange(10, dtype=np.float32)
    dataset = WindowDataset(values, labels, np.asarray([3, 8]), window_size=4)

    window, label = dataset[1]

    assert window.numpy().tolist() == values[5:9].tolist()
    assert label.item() == 8.0


def test_checkpoint_reconstructs_inference_model(tmp_path) -> None:
    model = LSTMClassifier(input_size=3, hidden_size=5, dropout=0.0)
    checkpoint = tmp_path / "model.pt"
    torch.save(
        {
            "model": "lstm",
            "state_dict": model.state_dict(),
            "window_size": 4,
            "input_size": 3,
            "preprocessor": {"output_features": ["a", "b", "c"]},
            "config": {"hidden_size": 5, "num_layers": 1, "dropout": 0.0},
        },
        checkpoint,
    )

    restored, metadata = load_sequence_checkpoint(checkpoint)

    assert metadata["window_size"] == 4
    assert torch.allclose(model(torch.ones(2, 4, 3)), restored(torch.ones(2, 4, 3)))
