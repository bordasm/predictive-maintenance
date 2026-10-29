from __future__ import annotations

from predictive_maintenance.data.features import build_feature_table
from predictive_maintenance.data.load import RawTables
from predictive_maintenance.data.split import assign_machine_splits


def test_machine_splits_are_disjoint_and_reproducible(raw_tables: RawTables) -> None:
    features = build_feature_table(
        raw_tables, horizon_hours=24, rolling_windows_hours=(3,)
    )
    first, first_manifest = assign_machine_splits(
        features, train_fraction=0.5, validation_fraction=0.25, random_seed=7
    )
    second, second_manifest = assign_machine_splits(
        features, train_fraction=0.5, validation_fraction=0.25, random_seed=7
    )

    assert first_manifest == second_manifest
    assert first["split"].tolist() == second["split"].tolist()
    split_sets = [set(values) for values in first_manifest.values()]
    assert split_sets[0].isdisjoint(split_sets[1])
    assert split_sets[0].isdisjoint(split_sets[2])
    assert split_sets[1].isdisjoint(split_sets[2])
