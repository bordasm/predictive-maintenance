"""Call the three public inference endpoints and fail on any HTTP error."""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path


def _json_request(url: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--payload", type=Path, default=Path("examples/prediction_request.json")
    )
    args = parser.parse_args()
    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    results = {
        "health": _json_request(f"{args.base_url}/health"),
        "model_info": _json_request(f"{args.base_url}/v1/model-info"),
        "prediction": _json_request(f"{args.base_url}/v1/predict", payload),
    }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
