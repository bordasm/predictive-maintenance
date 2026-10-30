"""Reference profiles, drift metrics, and delayed-label evaluation."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

EPSILON = 1e-6


def _distribution(values: pd.Series, boundaries: list[float]) -> list[float]:
    bins = np.asarray([-np.inf, *boundaries, np.inf], dtype=float)
    counts, _ = np.histogram(values.dropna().astype(float), bins=bins)
    proportions = counts / max(counts.sum(), 1)
    return proportions.tolist()


def _psi(reference: list[float], current: list[float]) -> float:
    expected = np.clip(np.asarray(reference, dtype=float), EPSILON, None)
    actual = np.clip(np.asarray(current, dtype=float), EPSILON, None)
    return float(np.sum((actual - expected) * np.log(actual / expected)))


def build_reference_profile(
    frame: pd.DataFrame,
    *,
    feature_names: list[str],
    probabilities: np.ndarray | None = None,
    threshold: float | None = None,
    quantile_bins: int = 10,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize the model input distribution used as the drift baseline."""
    numeric: dict[str, Any] = {}
    categorical: dict[str, Any] = {}
    for name in feature_names:
        values = frame[name]
        if pd.api.types.is_numeric_dtype(values):
            quantiles = np.linspace(0, 1, quantile_bins + 1)[1:-1]
            boundaries = sorted(
                {float(value) for value in values.dropna().quantile(quantiles)}
            )
            numeric[name] = {
                "boundaries": boundaries,
                "distribution": _distribution(values, boundaries),
                "minimum": float(values.min()),
                "maximum": float(values.max()),
                "mean": float(values.mean()),
                "std": float(values.std(ddof=0)),
            }
        else:
            proportions = values.astype(str).value_counts(normalize=True)
            categorical[name] = {
                "distribution": {
                    str(key): float(value) for key, value in proportions.items()
                }
            }

    profile: dict[str, Any] = {
        "row_count": int(len(frame)),
        "feature_names": feature_names,
        "numeric": numeric,
        "categorical": categorical,
        "metadata": metadata or {},
    }
    if probabilities is not None:
        probability_series = pd.Series(probabilities, dtype=float)
        boundaries = sorted(
            {
                float(value)
                for value in probability_series.quantile(
                    np.linspace(0, 1, quantile_bins + 1)[1:-1]
                )
            }
        )
        profile["prediction"] = {
            "boundaries": boundaries,
            "distribution": _distribution(probability_series, boundaries),
            "mean": float(probability_series.mean()),
            "alert_rate": float((probability_series >= float(threshold)).mean()),
        }
    return profile


def _status(value: float, warning: float, critical: float) -> str:
    if value >= critical:
        return "critical"
    if value >= warning:
        return "warning"
    return "normal"


def evaluate_monitoring_window(
    reference: dict[str, Any],
    current: pd.DataFrame,
    *,
    warning_psi: float = 0.1,
    critical_psi: float = 0.2,
    warning_categorical_distance: float = 0.1,
    critical_categorical_distance: float = 0.2,
    labels: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Evaluate quality, feature drift, prediction drift, and known outcomes."""
    missing_columns = sorted(set(reference["feature_names"]) - set(current.columns))
    if missing_columns:
        raise ValueError(f"Monitoring data is missing columns: {missing_columns}")

    numeric_results: dict[str, Any] = {}
    for name, baseline in reference["numeric"].items():
        values = current[name]
        current_distribution = _distribution(values, baseline["boundaries"])
        psi = _psi(baseline["distribution"], current_distribution)
        out_of_range = float(
            ((values < baseline["minimum"]) | (values > baseline["maximum"])).mean()
        )
        numeric_results[name] = {
            "psi": psi,
            "status": _status(psi, warning_psi, critical_psi),
            "out_of_range_fraction": out_of_range,
            "current_mean": float(values.mean()),
        }

    categorical_results: dict[str, Any] = {}
    for name, baseline in reference["categorical"].items():
        expected = baseline["distribution"]
        actual = current[name].astype(str).value_counts(normalize=True).to_dict()
        categories = set(expected) | set(actual)
        distance = 0.5 * sum(
            abs(float(expected.get(key, 0)) - float(actual.get(key, 0)))
            for key in categories
        )
        unknown_fraction = float(
            (~current[name].astype(str).isin(expected.keys())).mean()
        )
        categorical_results[name] = {
            "total_variation_distance": distance,
            "status": _status(
                distance,
                warning_categorical_distance,
                critical_categorical_distance,
            ),
            "unknown_fraction": unknown_fraction,
        }

    prediction_result: dict[str, Any] | None = None
    if "prediction" in reference and "failure_probability" in current:
        baseline = reference["prediction"]
        distribution = _distribution(
            current["failure_probability"], baseline["boundaries"]
        )
        psi = _psi(baseline["distribution"], distribution)
        prediction_result = {
            "psi": psi,
            "status": _status(psi, warning_psi, critical_psi),
            "mean_probability": float(current["failure_probability"].mean()),
            "alert_rate": float(current["alert"].astype(bool).mean()),
        }

    performance: dict[str, Any] = {"status": "labels_not_provided"}
    if labels is not None and not labels.empty:
        required = {"observation_id", "actual_failure_within_horizon"}
        if not required.issubset(labels.columns):
            raise ValueError(f"Labels must contain columns: {sorted(required)}")
        joined = current.merge(labels[list(required)], on="observation_id", how="inner")
        if not joined.empty:
            truth = joined["actual_failure_within_horizon"].astype(int)
            alerts = joined["alert"].astype(int)
            matrix = confusion_matrix(truth, alerts, labels=[0, 1])
            performance = {
                "status": "evaluated",
                "labeled_rows": int(len(joined)),
                "label_coverage": float(len(joined) / len(current)),
                "average_precision": float(
                    average_precision_score(truth, joined["failure_probability"])
                ),
                "precision": float(precision_score(truth, alerts, zero_division=0)),
                "recall": float(recall_score(truth, alerts, zero_division=0)),
                "f1": float(f1_score(truth, alerts, zero_division=0)),
                "confusion_matrix": matrix.tolist(),
            }

    null_fractions = {
        name: float(current[name].isna().mean()) for name in reference["feature_names"]
    }
    duplicate_fraction = (
        float(current["observation_id"].duplicated().mean())
        if "observation_id" in current
        else 0.0
    )
    quality_status = (
        "critical"
        if duplicate_fraction > 0 or any(value > 0 for value in null_fractions.values())
        else "normal"
    )
    statuses = [item["status"] for item in numeric_results.values()]
    statuses.extend(item["status"] for item in categorical_results.values())
    statuses.append(quality_status)
    if prediction_result:
        statuses.append(prediction_result["status"])
    overall = "critical" if "critical" in statuses else (
        "warning" if "warning" in statuses else "normal"
    )
    return {
        "overall_status": overall,
        "row_count": int(len(current)),
        "data_quality": {
            "status": quality_status,
            "null_fractions": null_fractions,
            "duplicate_observation_fraction": duplicate_fraction,
        },
        "numeric_drift": numeric_results,
        "categorical_drift": categorical_results,
        "prediction_drift": prediction_result,
        "performance": performance,
    }
