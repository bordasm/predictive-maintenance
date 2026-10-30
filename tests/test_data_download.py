from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pytest

from predictive_maintenance.data.download import fetch_training_data
from predictive_maintenance.data.schema import TABLE_SCHEMAS


def _archive(path: Path, *, unsafe: bool = False) -> str:
    with zipfile.ZipFile(path, "w") as archive:
        for schema in TABLE_SCHEMAS.values():
            archive.writestr(f"nested/{schema.filename}", "header\n")
        if unsafe:
            archive.writestr("../outside.txt", "unsafe")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_verified_archive_is_extracted_to_canonical_directory(tmp_path: Path) -> None:
    archive = tmp_path / "training.zip"
    checksum = _archive(archive)
    output = tmp_path / "raw"

    result = fetch_training_data(archive.as_uri(), output, checksum)

    assert result["archive_sha256"] == checksum
    assert {path.name for path in output.iterdir()} == {
        schema.filename for schema in TABLE_SCHEMAS.values()
    }


def test_archive_checksum_is_mandatory(tmp_path: Path) -> None:
    archive = tmp_path / "training.zip"
    _archive(archive)

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        fetch_training_data(archive.as_uri(), tmp_path / "raw", "0" * 64)


def test_archive_path_traversal_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "training.zip"
    checksum = _archive(archive, unsafe=True)

    with pytest.raises(ValueError, match="Unsafe archive member"):
        fetch_training_data(archive.as_uri(), tmp_path / "raw", checksum)
