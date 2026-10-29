"""Load the five raw Azure predictive-maintenance CSV files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from predictive_maintenance.data.schema import TABLE_SCHEMAS


@dataclass(frozen=True)
class RawTables:
    telemetry: pd.DataFrame
    errors: pd.DataFrame
    maintenance: pd.DataFrame
    failures: pd.DataFrame
    machines: pd.DataFrame

    def as_dict(self) -> dict[str, pd.DataFrame]:
        return {
            "telemetry": self.telemetry,
            "errors": self.errors,
            "maintenance": self.maintenance,
            "failures": self.failures,
            "machines": self.machines,
        }


def _resolve_file(raw_dir: Path, filename: str) -> Path:
    candidate = raw_dir / filename
    if candidate.exists():
        return candidate

    # Some mirrors use an uppercase M in the machines filename.
    case_insensitive = {
        path.name.lower(): path for path in raw_dir.glob("*.csv") if path.is_file()
    }
    resolved = case_insensitive.get(filename.lower())
    if resolved is None:
        raise FileNotFoundError(f"Missing raw data file: {candidate}")
    return resolved


def load_raw_tables(raw_dir: str | Path) -> RawTables:
    """Load raw tables and parse event timestamps without modifying source files."""
    directory = Path(raw_dir)
    if not directory.is_dir():
        raise FileNotFoundError(f"Raw data directory does not exist: {directory}")

    loaded: dict[str, pd.DataFrame] = {}
    for name, schema in TABLE_SCHEMAS.items():
        path = _resolve_file(directory, schema.filename)
        frame = pd.read_csv(path)
        if schema.datetime_column and schema.datetime_column in frame.columns:
            frame[schema.datetime_column] = pd.to_datetime(
                frame[schema.datetime_column], errors="raise"
            )
        loaded[name] = frame

    return RawTables(**loaded)
