from __future__ import annotations

import numpy as np
import pandas as pd

from predictive_maintenance.sequence.data import (
    SequencePreprocessor,
    build_window_end_indices,
)


def _frame() -> pd.DataFrame:
    rows = []
    for machine_id, model in ((1, "model1"), (2, "model2")):
        for offset, timestamp in enumerate(pd.date_range("2026-01-01", periods=5, freq="h")):
            rows.append(
                {
                    "machineID": machine_id,
                    "datetime": timestamp,
                    "volt": float(machine_id * 10 + offset),
                    "model": model,
                    "failure_within_horizon": int(offset == 3),
                    "split": "train",
                }
            )
    return pd.DataFrame(rows)


def test_windows_never_cross_machine_boundaries_and_keep_positive_rows() -> None:
    frame = _frame()

    endpoints = build_window_end_indices(frame, window_size=3)
    sampled = build_window_end_indices(
        frame, window_size=3, stride=3, preserve_positive_labels=True
    )

    assert endpoints.tolist() == [2, 3, 4, 7, 8, 9]
    assert sampled.tolist() == [2, 3, 7, 8]
    for endpoint in endpoints:
        window = frame.iloc[endpoint - 2 : endpoint + 1]
        assert window["machineID"].nunique() == 1


def test_time_gaps_do_not_form_windows() -> None:
    frame = _frame().iloc[:5].copy()
    frame.loc[3:, "datetime"] += pd.Timedelta(hours=2)

    endpoints = build_window_end_indices(frame, window_size=3)

    assert endpoints.tolist() == [2]


def test_preprocessor_is_fitted_only_on_training_values() -> None:
    train = _frame()
    preprocessor = SequencePreprocessor.fit(train)
    validation = train.iloc[:1].copy()
    validation["volt"] = 1_000_000.0
    validation["model"] = "unseen-model"

    transformed = preprocessor.transform(validation)

    assert preprocessor.mean[0] == np.mean(train["volt"])
    assert transformed.shape == (1, 3)
    assert transformed[0, -2:].tolist() == [0.0, 0.0]
