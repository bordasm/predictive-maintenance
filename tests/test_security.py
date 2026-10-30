from __future__ import annotations

from pathlib import Path

import yaml

from predictive_maintenance.serving.security import valid_request_id


def test_request_id_validation_is_bounded() -> None:
    assert valid_request_id("trace-123_ABC.example")
    assert not valid_request_id(None)
    assert not valid_request_id("contains spaces")
    assert not valid_request_id("x" * 65)


def test_deployment_manifests_apply_security_contract() -> None:
    root = Path(__file__).parents[1]
    deployment = yaml.safe_load(
        (root / "deploy/kubernetes/base/deployment.yaml").read_text(encoding="utf-8")
    )
    container = deployment["spec"]["template"]["spec"]["containers"][0]
    pod_security = deployment["spec"]["template"]["spec"]["securityContext"]
    container_security = container["securityContext"]
    environment = {item["name"]: item for item in container["env"]}

    assert deployment["spec"]["replicas"] == 1
    assert deployment["spec"]["strategy"]["type"] == "Recreate"
    assert deployment["spec"]["template"]["spec"]["automountServiceAccountToken"] is False
    assert pod_security["runAsNonRoot"] is True
    assert container_security["readOnlyRootFilesystem"] is True
    assert container_security["allowPrivilegeEscalation"] is False
    assert container_security["capabilities"]["drop"] == ["ALL"]
    assert "requests" in container["resources"]
    assert "limits" in container["resources"]
    assert environment["PREDMAINT_API_KEY"]["valueFrom"]["secretKeyRef"]["key"] == "api-key"


def test_security_workflow_and_compose_are_hardened() -> None:
    root = Path(__file__).parents[1]
    workflow = yaml.safe_load(
        (root / ".github/workflows/security.yml").read_text(encoding="utf-8")
    )
    compose = yaml.safe_load((root / "compose.yaml").read_text(encoding="utf-8"))
    api = compose["services"]["inference-api"]

    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["codeql"]["permissions"]["security-events"] == "write"
    assert api["read_only"] is True
    assert api["cap_drop"] == ["ALL"]
    assert api["security_opt"] == ["no-new-privileges:true"]
