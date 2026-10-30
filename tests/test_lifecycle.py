from __future__ import annotations

import json
from pathlib import Path

from predictive_maintenance.lifecycle import ensure_incumbent_manifest


def test_clean_workspace_is_seeded_without_overwriting_incumbent(tmp_path: Path) -> None:
    incumbent = tmp_path / "artifacts" / "champion.json"
    promotion = tmp_path / "promotion.toml"
    promotion.write_text(
        f'[incumbent]\nmanifest_path = "{incumbent.as_posix()}"\n', encoding="utf-8"
    )
    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps(
            {
                "model": "benchmark",
                "mlflow_run_id": "seed-run",
                "metrics": {"validation": {}, "test": {}},
            }
        ),
        encoding="utf-8",
    )
    config = {
        "pipeline": {"promotion_config": str(promotion)},
        "automation": {"incumbent_seed_path": str(seed)},
    }

    assert ensure_incumbent_manifest(config) is True
    incumbent.write_text('{"model": "production"}', encoding="utf-8")
    assert ensure_incumbent_manifest(config) is False
    assert json.loads(incumbent.read_text()) == {"model": "production"}
