"""Download and safely unpack the raw training-data archive."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from predictive_maintenance.data.schema import TABLE_SCHEMAS

MAX_ARCHIVE_BYTES = 1_000_000_000
MAX_UNPACKED_BYTES = 2_000_000_000
MAX_ARCHIVE_MEMBERS = 2_000


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"https", "file"}:
        raise ValueError("Training-data URL must use HTTPS (or file:// for local tests)")
    request = urllib.request.Request(url, headers={"User-Agent": "predmaint-training/1"})
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as output:
        length = response.headers.get("Content-Length")
        if length is not None and int(length) > MAX_ARCHIVE_BYTES:
            raise ValueError("Training-data archive exceeds the download limit")
        copied = 0
        while chunk := response.read(1024 * 1024):
            copied += len(chunk)
            if copied > MAX_ARCHIVE_BYTES:
                raise ValueError("Training-data archive exceeds the download limit")
            output.write(chunk)


def _safe_members(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members = archive.infolist()
    if len(members) > MAX_ARCHIVE_MEMBERS:
        raise ValueError("Training-data archive has too many members")
    if sum(member.file_size for member in members) > MAX_UNPACKED_BYTES:
        raise ValueError("Training-data archive exceeds the unpacked-size limit")
    for member in members:
        path = PurePosixPath(member.filename.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Unsafe archive member: {member.filename}")
        unix_mode = member.external_attr >> 16
        if unix_mode & 0o170000 == 0o120000:
            raise ValueError(f"Archive symlinks are not allowed: {member.filename}")
    return members


def fetch_training_data(url: str, output_dir: str | Path, expected_sha256: str) -> dict[str, str]:
    if not expected_sha256:
        raise ValueError("An expected SHA-256 checksum is required")
    expected_sha256 = expected_sha256.strip().lower()
    if len(expected_sha256) != 64 or any(character not in "0123456789abcdef" for character in expected_sha256):
        raise ValueError("Expected SHA-256 must contain exactly 64 hexadecimal characters")

    output = Path(output_dir)
    required_names = {schema.filename for schema in TABLE_SCHEMAS.values()}
    with tempfile.TemporaryDirectory(prefix="predmaint-data-") as temporary:
        temporary_path = Path(temporary)
        archive_path = temporary_path / "training-data.zip"
        _download(url, archive_path)
        actual_sha256 = _sha256(archive_path)
        if actual_sha256 != expected_sha256:
            raise ValueError(
                f"Training-data SHA-256 mismatch: expected {expected_sha256}, got {actual_sha256}"
            )

        extracted = temporary_path / "extracted"
        with zipfile.ZipFile(archive_path) as archive:
            members = _safe_members(archive)
            archive.extractall(extracted, members=members)

        found: dict[str, Path] = {}
        for path in extracted.rglob("*"):
            if path.is_file() and path.name in required_names:
                if path.name in found:
                    raise ValueError(f"Duplicate required data file: {path.name}")
                found[path.name] = path
        missing = sorted(required_names.difference(found))
        if missing:
            raise ValueError(f"Training-data archive is missing: {', '.join(missing)}")

        output.mkdir(parents=True, exist_ok=True)
        for name, source in found.items():
            shutil.copy2(source, output / name)

    return {"archive_sha256": actual_sha256, "output_directory": str(output)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("PREDMAINT_DATA_URL"))
    parser.add_argument(
        "--sha256", default=os.environ.get("PREDMAINT_DATA_SHA256", "")
    )
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/azure_pdm"))
    args = parser.parse_args()
    if not args.url:
        parser.error("--url or PREDMAINT_DATA_URL is required")
    result = fetch_training_data(args.url, args.output_dir, args.sha256)
    print(f"Verified {result['archive_sha256']} and extracted to {result['output_directory']}")


if __name__ == "__main__":
    main()
