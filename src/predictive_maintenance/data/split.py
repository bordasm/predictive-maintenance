"""Deterministic, machine-disjoint dataset splitting."""

from __future__ import annotations

import numpy as np
import pandas as pd


def assign_machine_splits(
    frame: pd.DataFrame,
    *,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
    random_seed: int = 42,
) -> tuple[pd.DataFrame, dict[str, list[int]]]:
    """Assign each machine wholly to train, validation, or test."""
    if train_fraction <= 0 or validation_fraction <= 0:
        raise ValueError("train and validation fractions must be positive")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("train + validation fractions must be below 1")

    machines = np.asarray(sorted(frame["machineID"].unique()))
    if len(machines) < 3:
        raise ValueError("at least three machines are required for a three-way split")

    rng = np.random.default_rng(random_seed)
    rng.shuffle(machines)
    train_end = max(1, int(np.floor(len(machines) * train_fraction)))
    validation_count = max(1, int(np.floor(len(machines) * validation_fraction)))
    validation_end = min(len(machines) - 1, train_end + validation_count)

    manifest = {
        "train": sorted(int(value) for value in machines[:train_end]),
        "validation": sorted(int(value) for value in machines[train_end:validation_end]),
        "test": sorted(int(value) for value in machines[validation_end:]),
    }
    if not all(manifest.values()):
        raise ValueError("split fractions produced an empty partition")

    machine_to_split = {
        machine_id: split_name
        for split_name, machine_ids in manifest.items()
        for machine_id in machine_ids
    }
    result = frame.copy()
    result["split"] = result["machineID"].map(machine_to_split)
    if result["split"].isna().any():
        raise RuntimeError("one or more machines were not assigned to a split")
    return result, manifest
