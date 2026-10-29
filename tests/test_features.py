from __future__ import annotations

import pandas as pd

from predictive_maintenance.data.features import build_feature_table, label_upcoming_failures
from predictive_maintenance.data.load import RawTables


def test_failure_label_excludes_now_and_includes_horizon_boundary() -> None:
    telemetry = pd.DataFrame(
        {
            "machineID": [1, 1, 1],
            "datetime": pd.to_datetime(
                ["2026-01-01 00:00", "2026-01-01 01:00", "2026-01-02 00:00"]
            ),
        }
    )
    failures = pd.DataFrame(
        {"machineID": [1], "datetime": pd.to_datetime(["2026-01-02 00:00"])}
    )
    labels = label_upcoming_failures(telemetry, failures, horizon_hours=24)
    assert labels.tolist() == [1, 1, 0]


def test_error_history_never_uses_future_event(raw_tables: RawTables) -> None:
    features = build_feature_table(
        raw_tables, horizon_hours=24, rolling_windows_hours=(3,)
    )
    machine_one = features.loc[features["machineID"] == 1].reset_index(drop=True)
    assert machine_one.loc[4, "error1_count_24h"] == 0
    assert machine_one.loc[5, "error1_count_24h"] == 1
    assert machine_one.loc[6, "error1_count_24h"] == 1
