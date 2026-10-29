"""Metrics for rare-event predictive-maintenance classification."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)


def choose_f1_threshold(y_true: pd.Series, probabilities: np.ndarray) -> float:
    """Choose a threshold on validation data only."""
    if y_true.nunique() < 2:
        raise ValueError("validation data must contain both classes")
    precision, recall, thresholds = precision_recall_curve(y_true, probabilities)
    if not len(thresholds):
        return 0.5
    denominator = precision[:-1] + recall[:-1]
    f1_values = np.divide(
        2 * precision[:-1] * recall[:-1],
        denominator,
        out=np.zeros_like(denominator),
        where=denominator > 0,
    )
    return float(thresholds[int(np.nanargmax(f1_values))])


def classification_report(
    frame: pd.DataFrame,
    probabilities: np.ndarray,
    *,
    threshold: float,
) -> dict[str, object]:
    y_true = frame["failure_within_horizon"].astype(int)
    predictions = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()
    machine_days = max(
        1,
        frame.assign(day=frame["datetime"].dt.date)[["machineID", "day"]]
        .drop_duplicates()
        .shape[0],
    )
    roc_auc = float(roc_auc_score(y_true, probabilities)) if y_true.nunique() == 2 else None
    return {
        "rows": int(len(frame)),
        "positive_rows": int(y_true.sum()),
        "positive_rate": float(y_true.mean()),
        "threshold": float(threshold),
        "average_precision": float(average_precision_score(y_true, probabilities)),
        "roc_auc": roc_auc,
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "false_positive_rows_per_machine_day": float(fp / machine_days),
        "false_positive_rows_per_machine_week": float(7 * fp / machine_days),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
    }


def failure_event_report(
    frame: pd.DataFrame,
    probabilities: np.ndarray,
    failures: pd.DataFrame,
    *,
    threshold: float,
    horizon_hours: int,
) -> dict[str, int | float | None]:
    """Measure whether each eligible failure received an advance warning."""
    if len(frame) != len(probabilities):
        raise ValueError("frame and probabilities must contain the same number of rows")

    predictions = frame[["machineID", "datetime"]].copy()
    predictions["alert"] = probabilities >= threshold
    horizon = pd.Timedelta(hours=horizon_hours)
    lead_times: list[float] = []
    eligible_events = 0

    test_failures = failures.loc[failures["machineID"].isin(frame["machineID"].unique())]
    for failure in test_failures.itertuples(index=False):
        window = predictions.loc[
            (predictions["machineID"] == failure.machineID)
            & (predictions["datetime"] >= failure.datetime - horizon)
            & (predictions["datetime"] < failure.datetime)
        ]
        if window.empty:
            continue
        eligible_events += 1
        alerts = window.loc[window["alert"]]
        if not alerts.empty:
            first_alert = alerts["datetime"].min()
            lead_times.append((failure.datetime - first_alert).total_seconds() / 3600)

    detected_events = len(lead_times)
    return {
        "eligible_failure_events": eligible_events,
        "detected_failure_events": detected_events,
        "event_recall": (
            float(detected_events / eligible_events) if eligible_events else None
        ),
        "median_lead_time_hours": (
            float(np.median(lead_times)) if lead_times else None
        ),
    }
