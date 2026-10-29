"""Fail-fast data-quality checks for the raw source tables."""

from __future__ import annotations

import pandas as pd

from predictive_maintenance.data.load import RawTables
from predictive_maintenance.data.schema import COMPONENT_IDS, ERROR_IDS, TABLE_SCHEMAS


class DataValidationError(ValueError):
    """Raised when raw data violates the declared data contract."""


def _require_columns(name: str, frame: pd.DataFrame) -> None:
    required = set(TABLE_SCHEMAS[name].columns)
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise DataValidationError(f"{name}: missing columns: {missing}")


def validate_raw_tables(tables: RawTables, *, require_hourly: bool = True) -> None:
    """Validate schemas, keys, categories, nulls, and telemetry cadence."""
    table_map = tables.as_dict()
    for name, frame in table_map.items():
        _require_columns(name, frame)
        required_columns = list(TABLE_SCHEMAS[name].columns)
        null_counts = frame[required_columns].isna().sum()
        null_counts = null_counts[null_counts > 0]
        if not null_counts.empty:
            raise DataValidationError(f"{name}: null values: {null_counts.to_dict()}")

    if tables.machines["machineID"].duplicated().any():
        raise DataValidationError("machines: machineID must be unique")

    duplicate_telemetry = tables.telemetry.duplicated(["machineID", "datetime"])
    if duplicate_telemetry.any():
        raise DataValidationError(
            f"telemetry: {int(duplicate_telemetry.sum())} duplicate machine/timestamp rows"
        )

    machine_ids = set(tables.machines["machineID"])
    for name in ("telemetry", "errors", "maintenance", "failures"):
        unknown = sorted(set(table_map[name]["machineID"]).difference(machine_ids))
        if unknown:
            raise DataValidationError(f"{name}: unknown machine IDs: {unknown[:10]}")

    invalid_errors = sorted(set(tables.errors["errorID"]).difference(ERROR_IDS))
    if invalid_errors:
        raise DataValidationError(f"errors: invalid errorID values: {invalid_errors}")

    invalid_maintenance = sorted(set(tables.maintenance["comp"]).difference(COMPONENT_IDS))
    if invalid_maintenance:
        raise DataValidationError(
            f"maintenance: invalid component values: {invalid_maintenance}"
        )

    invalid_failures = sorted(set(tables.failures["failure"]).difference(COMPONENT_IDS))
    if invalid_failures:
        raise DataValidationError(f"failures: invalid failure values: {invalid_failures}")

    if require_hourly:
        ordered = tables.telemetry.sort_values(["machineID", "datetime"])
        deltas = ordered.groupby("machineID", sort=False)["datetime"].diff().dropna()
        invalid_count = int((deltas != pd.Timedelta(hours=1)).sum())
        if invalid_count:
            raise DataValidationError(
                f"telemetry: expected hourly cadence; found {invalid_count} irregular intervals"
            )
