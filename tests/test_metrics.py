from __future__ import annotations

import numpy as np
import pandas as pd

from predictive_maintenance.evaluation.metrics import failure_event_report


def test_failure_event_report_uses_strictly_prior_alerts() -> None:
    frame = pd.DataFrame(
        {
            "machineID": [1, 1, 1, 1],
            "datetime": pd.to_datetime(
                [
                    "2024-01-01 00:00:00",
                    "2024-01-01 12:00:00",
                    "2024-01-02 00:00:00",
                    "2024-01-02 12:00:00",
                ]
            ),
        }
    )
    failures = pd.DataFrame(
        {
            "machineID": [1],
            "datetime": pd.to_datetime(["2024-01-02 00:00:00"]),
            "failure": ["comp1"],
        }
    )

    report = failure_event_report(
        frame,
        np.array([0.1, 0.9, 0.99, 0.1]),
        failures,
        threshold=0.5,
        horizon_hours=24,
    )

    assert report["eligible_failure_events"] == 1
    assert report["detected_failure_events"] == 1
    assert report["event_recall"] == 1.0
    assert report["median_lead_time_hours"] == 12.0


def test_failure_event_report_handles_no_eligible_events() -> None:
    frame = pd.DataFrame(
        {
            "machineID": [1],
            "datetime": pd.to_datetime(["2024-01-02 00:00:00"]),
        }
    )
    failures = pd.DataFrame(
        {
            "machineID": [2],
            "datetime": pd.to_datetime(["2024-01-02 00:00:00"]),
            "failure": ["comp1"],
        }
    )

    report = failure_event_report(
        frame,
        np.array([0.9]),
        failures,
        threshold=0.5,
        horizon_hours=24,
    )

    assert report["eligible_failure_events"] == 0
    assert report["event_recall"] is None
    assert report["median_lead_time_hours"] is None
