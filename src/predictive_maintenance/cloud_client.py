"""Client for testing the deployed Firebase-authenticated Google Cloud API."""

from __future__ import annotations

import argparse
import getpass
import json
import re
import sys
import urllib.error
import urllib.request
import uuid
from typing import Any


DEFAULT_DASHBOARD_URL = "https://predmaint-dashboard-agq2q67cmq-ew.a.run.app"
CONFIG_PATTERN = re.compile(r"window\.PREDMAINT_CONFIG\s*=\s*({.*?})\s*;", re.DOTALL)


class ClientError(RuntimeError):
    """A safe, user-facing cloud client error."""


def _request_json(
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    token: str | None = None,
    timeout: float = 60,
) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST" if payload is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            body = json.load(error)
        except (json.JSONDecodeError, UnicodeDecodeError):
            body = {}
        message = body.get("error", {}).get("message") or body.get("detail")
        if error.code in {401, 403}:
            message = message or "authentication failed or access was denied"
        raise ClientError(f"HTTP {error.code}: {message or error.reason}") from None
    except (OSError, TimeoutError) as error:
        raise ClientError(f"The service could not be reached: {error}") from None


def parse_runtime_config(source: str) -> dict[str, str]:
    """Extract the public Firebase and API settings emitted by the dashboard."""
    match = CONFIG_PATTERN.search(source)
    if not match:
        raise ClientError("The dashboard runtime configuration is not valid")
    try:
        config = json.loads(match.group(1))
    except json.JSONDecodeError as error:
        raise ClientError("The dashboard runtime configuration is not valid") from error
    required = ("apiBaseUrl", "firebaseApiKey", "firebaseProjectId")
    if any(not isinstance(config.get(key), str) or not config[key] for key in required):
        raise ClientError("The dashboard runtime configuration is incomplete")
    return {key: config[key].rstrip("/") for key in required}


def load_runtime_config(dashboard_url: str, timeout: float) -> dict[str, str]:
    request = urllib.request.Request(
        f"{dashboard_url.rstrip('/')}/config.js",
        headers={"Accept": "application/javascript"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            source = response.read().decode("utf-8")
    except (urllib.error.HTTPError, OSError, TimeoutError) as error:
        raise ClientError(f"The dashboard configuration could not be loaded: {error}") from None
    return parse_runtime_config(source)


def sign_in(firebase_api_key: str, email: str, password: str, timeout: float) -> str:
    endpoint = (
        "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
        f"?key={firebase_api_key}"
    )
    response = _request_json(
        endpoint,
        payload={"email": email, "password": password, "returnSecureToken": True},
        timeout=timeout,
    )
    token = response.get("idToken")
    if not isinstance(token, str) or not token:
        raise ClientError("Firebase did not return an ID token")
    return token


def build_prediction_payload(sample: dict[str, Any]) -> dict[str, Any]:
    """Convert one held-out demo sample into the versioned inference contract."""
    return {
        "observations": [
            {
                "observation_id": f"python-client-{sample['sample_id']}-{uuid.uuid4()}",
                "machine_id": sample["machine_id"],
                "observed_at": sample["observed_at"],
                "features": sample["features"],
            }
        ]
    }


def _choose_sample(samples: list[dict[str, Any]], requested_index: int | None) -> int:
    if requested_index is not None:
        index = requested_index
    elif sys.stdin.isatty():
        answer = input(f"Test sample [0-{len(samples) - 1}, default 0]: ").strip()
        index = int(answer) if answer else 0
    else:
        index = 0
    if not 0 <= index < len(samples):
        raise ClientError(f"Sample index must be between 0 and {len(samples) - 1}")
    return index


def _print_samples(samples: list[dict[str, Any]]) -> None:
    print("\nHeld-out test samples:")
    for index, sample in enumerate(samples):
        component = sample.get("failure_component") or "none"
        print(
            f"  [{index}] machine={sample['machine_id']} "
            f"observed_at={sample['observed_at']} "
            f"failure_within_horizon={sample['actual_failure_within_horizon']} "
            f"component={component}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dashboard-url", default=DEFAULT_DASHBOARD_URL)
    parser.add_argument("--api-url", help="Override the API URL published by the dashboard")
    parser.add_argument("--email", help="Firebase user email; prompted when omitted")
    parser.add_argument("--sample-index", type=int)
    parser.add_argument("--list-only", action="store_true", help="Do not run inference")
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()

    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    try:
        config = load_runtime_config(args.dashboard_url, args.timeout)
        api_url = (args.api_url or config["apiBaseUrl"]).rstrip("/")
        email = args.email or input("Firebase email: ").strip()
        if not email:
            raise ClientError("An email address is required")
        password = getpass.getpass("Firebase password: ")
        if not password:
            raise ClientError("A password is required")

        token = sign_in(config["firebaseApiKey"], email, password, args.timeout)
        model = _request_json(f"{api_url}/v1/model-info", token=token, timeout=args.timeout)
        dataset = _request_json(
            f"{api_url}/v1/demo-samples", token=token, timeout=args.timeout
        )
        samples = dataset.get("samples")
        if not isinstance(samples, list) or not samples:
            raise ClientError("The deployment returned no held-out test samples")

        print(f"\nConnected: {api_url}")
        print(
            f"Champion: {model['model']} | version={model['model_version']} | "
            f"threshold={model['threshold']} | features={model['feature_count']}"
        )
        _print_samples(samples)
        if args.list_only:
            return 0

        sample = samples[_choose_sample(samples, args.sample_index)]
        response = _request_json(
            f"{api_url}/v1/predict",
            payload=build_prediction_payload(sample),
            token=token,
            timeout=args.timeout,
        )
        prediction = response["predictions"][0]
        print("\nInference result:")
        print(json.dumps(prediction, indent=2))
        print(
            "Held-out outcome: "
            f"failure_within_horizon={sample['actual_failure_within_horizon']}, "
            f"component={sample.get('failure_component') or 'none'}"
        )
        return 0
    except (ClientError, KeyError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
