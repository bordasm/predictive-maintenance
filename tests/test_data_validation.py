from __future__ import annotations

import pandas as pd
import pytest

from predictive_maintenance.data.load import RawTables
from predictive_maintenance.data.validate import DataValidationError, validate_raw_tables


def test_valid_tables_pass(raw_tables: RawTables) -> None:
    validate_raw_tables(raw_tables)


def test_duplicate_telemetry_is_rejected(raw_tables: RawTables) -> None:
    duplicated = pd.concat([raw_tables.telemetry, raw_tables.telemetry.iloc[[0]]])
    invalid = RawTables(
        duplicated,
        raw_tables.errors,
        raw_tables.maintenance,
        raw_tables.failures,
        raw_tables.machines,
    )
    with pytest.raises(DataValidationError, match="duplicate"):
        validate_raw_tables(invalid)
