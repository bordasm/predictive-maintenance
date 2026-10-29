from __future__ import annotations

from predictive_maintenance.data.features import build_feature_table
from predictive_maintenance.data.load import RawTables
from predictive_maintenance.data.split import assign_machine_splits
from predictive_maintenance.models.baseline import feature_columns, predict_probabilities
from predictive_maintenance.models.challenger import build_challenger_model


def test_challenger_fits_and_predicts_probabilities(raw_tables: RawTables) -> None:
    frame = build_feature_table(raw_tables)
    frame, _ = assign_machine_splits(frame)
    train = frame.loc[frame["split"] == "train"]
    test = frame.loc[frame["split"] == "test"]
    numerical_columns, categorical_columns = feature_columns(train)
    features = numerical_columns + categorical_columns
    model = build_challenger_model(
        numerical_columns,
        categorical_columns,
        max_iterations=5,
        min_samples_leaf=5,
    )

    model.fit(train[features], train["failure_within_horizon"])
    probabilities = predict_probabilities(model, test[features])

    assert len(probabilities) == len(test)
    assert ((0.0 <= probabilities) & (probabilities <= 1.0)).all()
