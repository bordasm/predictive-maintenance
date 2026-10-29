from __future__ import annotations

import pandas as pd
import pytest

from predictive_maintenance.data.load import RawTables


@pytest.fixture
def raw_tables() -> RawTables:
    timestamps = pd.date_range("2026-01-01", periods=30, freq="h")
    telemetry_rows = []
    for machine_id in range(1, 7):
        for offset, timestamp in enumerate(timestamps):
            telemetry_rows.append(
                {
                    "datetime": timestamp,
                    "machineID": machine_id,
                    "volt": 100.0 + machine_id + offset * 0.1,
                    "rotate": 400.0 + machine_id,
                    "pressure": 90.0 + offset * 0.05,
                    "vibration": 40.0 + machine_id * 0.1,
                }
            )
    telemetry = pd.DataFrame(telemetry_rows)
    machines = pd.DataFrame(
        {
            "machineID": range(1, 7),
            "model": ["model1", "model2"] * 3,
            "age": [3, 4, 5, 6, 7, 8],
        }
    )
    errors = pd.DataFrame(
        [
            {"datetime": timestamps[5], "machineID": machine_id, "errorID": "error1"}
            for machine_id in range(1, 7)
        ]
    )
    maintenance = pd.DataFrame(
        [
            {"datetime": timestamps[2], "machineID": machine_id, "comp": "comp1"}
            for machine_id in range(1, 7)
        ]
    )
    failures = pd.DataFrame(
        [
            {"datetime": timestamps[25], "machineID": machine_id, "failure": "comp1"}
            for machine_id in range(1, 7)
        ]
    )
    return RawTables(telemetry, errors, maintenance, failures, machines)
