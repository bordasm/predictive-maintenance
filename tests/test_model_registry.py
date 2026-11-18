from __future__ import annotations

from datetime import UTC, datetime

import pytest

torch = pytest.importorskip("torch")

from predictive_maintenance.sequence.models import LSTMClassifier  # noqa: E402
from predictive_maintenance.serving.model_registry import (  # noqa: E402
    SequenceInferenceModel,
)
from predictive_maintenance.serving.schemas import (  # noqa: E402
    FeatureVector,
    PredictionObservation,
)


def test_sequence_inference_model_scores_exact_window(tmp_path) -> None:
    model = LSTMClassifier(input_size=2, hidden_size=5, dropout=0.0)
    checkpoint = tmp_path / "lstm.pt"
    torch.save(
        {
            "model": "lstm",
            "state_dict": model.state_dict(),
            "window_size": 4,
            "input_size": 2,
            "preprocessor": {
                "numerical_columns": ["volt"],
                "categorical_column": "model",
                "categories": ["model1"],
                "mean": [100.0],
                "scale": [10.0],
            },
            "config": {"hidden_size": 5, "num_layers": 1, "dropout": 0.0},
        },
        checkpoint,
    )
    service = SequenceInferenceModel.load(
        {
            "model": "lstm",
            "model_path": str(checkpoint),
            "threshold": 0.5,
            "selection_metric": "average_precision",
            "selection_value": 0.9,
            "mlflow_run_id": "abcdef1234567890",
        },
        tmp_path / "registry.json",
    )
    values = {
        name: ("model1" if name == "model" else 1)
        for name in FeatureVector.model_fields
    }
    feature = FeatureVector.model_validate(values)
    observation = PredictionObservation(
        observation_id="test-window",
        machine_id=1,
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
        features=feature,
        sequence=[feature] * 4,
    )

    scores = service.predict([observation])

    assert len(scores) == 1
    assert 0 <= scores[0][0] <= 1
    assert scores[0][1] is (scores[0][0] >= 0.5)

    short = observation.model_copy(update={"sequence": [feature] * 3})
    with pytest.raises(ValueError, match="exactly 4 hourly rows"):
        service.predict([short])
