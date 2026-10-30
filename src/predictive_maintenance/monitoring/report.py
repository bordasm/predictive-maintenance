"""Serialize monitoring results for machines and human reviewers."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def write_monitoring_report(
    result: dict[str, Any], output_directory: str | Path, *, title: str
) -> tuple[Path, Path]:
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    document = {
        "generated_at": datetime.now(UTC).isoformat(),
        "title": title,
        **result,
    }
    json_path = output / "monitoring.json"
    markdown_path = output / "README.md"
    json_path.write_text(json.dumps(document, indent=2), encoding="utf-8")

    ranked_numeric = sorted(
        result["numeric_drift"].items(),
        key=lambda item: item[1]["psi"],
        reverse=True,
    )
    lines = [
        f"# {title}",
        "",
        f"**Overall status:** `{result['overall_status']}`  ",
        f"**Rows:** {result['row_count']}",
        "",
        "## Data quality",
        "",
        f"- Status: **{result['data_quality']['status']}**",
        "- Duplicate observation fraction: "
        f"**{result['data_quality']['duplicate_observation_fraction']:.2%}**",
        "- Features containing nulls: "
        f"**{sum(value > 0 for value in result['data_quality']['null_fractions'].values())}**",
        "",
        "## Strongest numeric drift signals",
        "",
        "| Feature | PSI | Status | Out of range |",
        "|---|---:|---|---:|",
    ]
    for name, metrics in ranked_numeric[:10]:
        lines.append(
            f"| `{name}` | {metrics['psi']:.4f} | {metrics['status']} | "
            f"{metrics['out_of_range_fraction']:.2%} |"
        )
    lines.extend(["", "## Prediction distribution", ""])
    prediction = result["prediction_drift"]
    if prediction:
        lines.extend(
            [
                f"- PSI: **{prediction['psi']:.4f}** ({prediction['status']})",
                f"- Mean failure probability: **{prediction['mean_probability']:.4f}**",
                f"- Alert rate: **{prediction['alert_rate']:.2%}**",
            ]
        )
    else:
        lines.append("Prediction probabilities were not available in this window.")
    lines.extend(["", "## Delayed-label performance", ""])
    performance = result["performance"]
    if performance["status"] == "evaluated":
        lines.extend(
            [
                f"- Labeled rows: **{performance['labeled_rows']}** "
                f"({performance['label_coverage']:.2%} coverage)",
                f"- Average precision: **{performance['average_precision']:.4f}**",
                f"- Precision / recall / F1: **{performance['precision']:.4f} / "
                f"{performance['recall']:.4f} / {performance['f1']:.4f}**",
            ]
        )
    else:
        lines.append("No delayed labels were supplied for this window.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "PSI below 0.10 is normal, 0.10–0.20 is a warning, and 0.20 or above "
            "is critical in this project. A critical result is a review trigger; it "
            "does not automatically retrain or promote a model.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, markdown_path
