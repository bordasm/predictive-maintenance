from __future__ import annotations

import numpy as np
import pandas as pd

from predictive_maintenance.monitoring.drift import (
    build_reference_profile,
    evaluate_monitoring_window,
)


def test_monitoring_detects_drift_and_evaluates_delayed_labels() -> None:
    rng = np.random.default_rng(42)
    rows = 2000
    reference_frame = pd.DataFrame(
        {
            "sensor": rng.normal(100, 5, rows),
            "age": rng.integers(1, 10, rows),
            "model": np.where(np.arange(rows) % 2, "model1", "model2"),
        }
    )
    reference_probabilities = np.linspace(0.01, 0.99, rows)
    profile = build_reference_profile(
        reference_frame,
        feature_names=["sensor", "age", "model"],
        probabilities=reference_probabilities,
        threshold=0.5,
    )
    current = reference_frame.copy()
    current.insert(0, "observation_id", [f"obs-{index}" for index in range(rows)])
    current["failure_probability"] = reference_probabilities
    current["alert"] = reference_probabilities >= 0.5
    labels = pd.DataFrame(
        {
            "observation_id": current["observation_id"],
            "actual_failure_within_horizon": current["alert"].astype(int),
        }
    )

    stable = evaluate_monitoring_window(profile, current, labels=labels)
    drifted_frame = current.copy()
    drifted_frame["sensor"] += 50
    drifted = evaluate_monitoring_window(profile, drifted_frame)

    assert stable["overall_status"] == "normal"
    assert stable["performance"]["status"] == "evaluated"
    assert stable["performance"]["f1"] == 1.0
    assert drifted["overall_status"] == "critical"
    assert drifted["numeric_drift"]["sensor"]["psi"] >= 0.2
    assert drifted["numeric_drift"]["sensor"]["out_of_range_fraction"] > 0.99
