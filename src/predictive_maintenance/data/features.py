"""Leakage-aware feature and label construction."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

from predictive_maintenance.data.load import RawTables
from predictive_maintenance.data.schema import COMPONENT_IDS, ERROR_IDS, SENSOR_COLUMNS


def label_upcoming_failures(
    telemetry: pd.DataFrame,
    failures: pd.DataFrame,
    *,
    horizon_hours: int,
) -> pd.Series:
    """Return 1 when the next failure is strictly after now and within the horizon."""
    if horizon_hours <= 0:
        raise ValueError("horizon_hours must be positive")

    labels = pd.Series(
        np.zeros(len(telemetry), dtype=np.int8),
        index=telemetry.index,
        name="failure_within_horizon",
    )
    telemetry_groups = telemetry.groupby("machineID", sort=False).groups
    failure_groups = {
        machine_id: np.sort(group["datetime"].to_numpy(dtype="datetime64[ns]"))
        for machine_id, group in failures.groupby("machineID", sort=False)
    }
    horizon = np.timedelta64(horizon_hours, "h")

    for machine_id, row_index in telemetry_groups.items():
        failure_times = failure_groups.get(machine_id)
        if failure_times is None or not len(failure_times):
            continue
        index_labels = pd.Index(row_index)
        observation_times = telemetry.loc[index_labels, "datetime"].to_numpy(
            dtype="datetime64[ns]"
        )
        next_positions = np.searchsorted(failure_times, observation_times, side="right")
        has_next = next_positions < len(failure_times)
        within_horizon = np.zeros(len(index_labels), dtype=bool)
        if has_next.any():
            deltas = (
                failure_times[next_positions[has_next]] - observation_times[has_next]
            )
            within_horizon[has_next] = deltas <= horizon
        labels.loc[index_labels] = within_horizon.astype(np.int8)

    return labels


def _add_sensor_history(frame: pd.DataFrame, windows: Iterable[int]) -> pd.DataFrame:
    for window in windows:
        if window <= 0:
            raise ValueError("rolling windows must be positive")
        rolling = frame.groupby("machineID", sort=False)[list(SENSOR_COLUMNS)].rolling(
            window=window, min_periods=1
        )
        means = rolling.mean().reset_index(level=0, drop=True)
        deviations = rolling.std(ddof=0).reset_index(level=0, drop=True)
        for sensor in SENSOR_COLUMNS:
            frame[f"{sensor}_mean_{window}h"] = means[sensor]
            frame[f"{sensor}_std_{window}h"] = deviations[sensor]
    return frame


def _add_error_history(frame: pd.DataFrame, errors: pd.DataFrame) -> pd.DataFrame:
    event_counts = (
        errors.assign(count=1)
        .pivot_table(
            index=["machineID", "datetime"],
            columns="errorID",
            values="count",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(columns=ERROR_IDS, fill_value=0)
        .reset_index()
    )
    frame = frame.merge(event_counts, on=["machineID", "datetime"], how="left")
    frame[list(ERROR_IDS)] = frame[list(ERROR_IDS)].fillna(0)
    rolling_counts = (
        frame.groupby("machineID", sort=False)[list(ERROR_IDS)]
        .rolling(window=24, min_periods=1)
        .sum()
        .reset_index(level=0, drop=True)
    )
    for error_id in ERROR_IDS:
        frame[f"{error_id}_count_24h"] = rolling_counts[error_id].astype(np.float32)
    return frame.drop(columns=list(ERROR_IDS))


def _add_maintenance_recency(
    frame: pd.DataFrame, maintenance: pd.DataFrame
) -> pd.DataFrame:
    telemetry_groups = frame.groupby("machineID", sort=False).groups
    default_days = 3650.0

    for component in COMPONENT_IDS:
        values = np.full(len(frame), default_days, dtype=np.float32)
        events = maintenance.loc[maintenance["comp"] == component]
        events_by_machine = {
            machine_id: np.sort(group["datetime"].to_numpy(dtype="datetime64[ns]"))
            for machine_id, group in events.groupby("machineID", sort=False)
        }
        for machine_id, row_index in telemetry_groups.items():
            event_times = events_by_machine.get(machine_id)
            if event_times is None or not len(event_times):
                continue
            index_array = np.asarray(row_index, dtype=int)
            observation_times = frame.loc[index_array, "datetime"].to_numpy(
                dtype="datetime64[ns]"
            )
            previous_positions = np.searchsorted(
                event_times, observation_times, side="right"
            ) - 1
            has_previous = previous_positions >= 0
            elapsed_days = np.full(len(index_array), default_days, dtype=np.float32)
            elapsed_days[has_previous] = (
                observation_times[has_previous]
                - event_times[previous_positions[has_previous]]
            ) / np.timedelta64(1, "D")
            values[index_array] = elapsed_days
        frame[f"days_since_{component}_maintenance"] = values
    return frame


def build_feature_table(
    tables: RawTables,
    *,
    horizon_hours: int = 24,
    rolling_windows_hours: Iterable[int] = (3, 24),
) -> pd.DataFrame:
    """Build features using information available at or before each observation."""
    frame = tables.telemetry.sort_values(["machineID", "datetime"]).reset_index(drop=True)
    frame = _add_sensor_history(frame, rolling_windows_hours)
    frame = _add_error_history(frame, tables.errors)
    frame = _add_maintenance_recency(frame, tables.maintenance)
    frame = frame.merge(tables.machines, on="machineID", how="left", validate="many_to_one")
    frame["failure_within_horizon"] = label_upcoming_failures(
        frame, tables.failures, horizon_hours=horizon_hours
    )
    return frame
