from __future__ import annotations

from scripts.gcp_api_client import build_prediction_payload, parse_runtime_config


def test_parse_runtime_config_extracts_public_cloud_settings() -> None:
    config = parse_runtime_config(
        'window.PREDMAINT_CONFIG = {"apiBaseUrl": "https://api.example/", '
        '"firebaseApiKey": "public-key", "firebaseProjectId": "demo-project"};\n'
    )

    assert config == {
        "apiBaseUrl": "https://api.example",
        "firebaseApiKey": "public-key",
        "firebaseProjectId": "demo-project",
    }


def test_prediction_payload_uses_held_out_sample(monkeypatch) -> None:
    monkeypatch.setattr("scripts.gcp_api_client.uuid.uuid4", lambda: "request-uuid")
    sample = {
        "sample_id": "held-out-7",
        "machine_id": 7,
        "observed_at": "2026-01-01T00:00:00Z",
        "features": {"volt": 170.0, "model": "model1"},
    }

    payload = build_prediction_payload(sample)

    assert payload == {
        "observations": [
            {
                "observation_id": "python-client-held-out-7-request-uuid",
                "machine_id": 7,
                "observed_at": "2026-01-01T00:00:00Z",
                "features": {"volt": 170.0, "model": "model1"},
            }
        ]
    }
