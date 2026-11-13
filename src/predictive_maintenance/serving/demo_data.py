"""Read held-out demonstration observations packaged with a deployment."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from predictive_maintenance.serving.schemas import FeatureVector


class DemoSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_id: str
    machine_id: int = Field(ge=1)
    observed_at: str
    actual_failure_within_horizon: bool
    failure_component: str | None = None
    features: FeatureVector


class DemoDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    split: str
    samples: list[DemoSample]


def load_demo_dataset(path: str | Path) -> DemoDataset:
    payload: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    return DemoDataset.model_validate(payload)
