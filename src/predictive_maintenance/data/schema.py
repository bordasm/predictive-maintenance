"""Schema declarations for the Microsoft Azure predictive-maintenance data."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TableSchema:
    filename: str
    columns: tuple[str, ...]
    datetime_column: str | None = None


TABLE_SCHEMAS: dict[str, TableSchema] = {
    "telemetry": TableSchema(
        "PdM_telemetry.csv",
        ("datetime", "machineID", "volt", "rotate", "pressure", "vibration"),
        "datetime",
    ),
    "errors": TableSchema(
        "PdM_errors.csv",
        ("datetime", "machineID", "errorID"),
        "datetime",
    ),
    "maintenance": TableSchema(
        "PdM_maint.csv",
        ("datetime", "machineID", "comp"),
        "datetime",
    ),
    "failures": TableSchema(
        "PdM_failures.csv",
        ("datetime", "machineID", "failure"),
        "datetime",
    ),
    "machines": TableSchema(
        "PdM_machines.csv",
        ("machineID", "model", "age"),
    ),
}

SENSOR_COLUMNS = ("volt", "rotate", "pressure", "vibration")
ERROR_IDS = tuple(f"error{i}" for i in range(1, 6))
COMPONENT_IDS = tuple(f"comp{i}" for i in range(1, 5))
