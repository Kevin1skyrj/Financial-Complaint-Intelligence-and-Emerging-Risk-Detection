"""Reproducible and safe acquisition of the official CFPB narrative archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO
from urllib.request import Request, urlopen

from complaint_intelligence.config import load_config


USER_AGENT = "financial-complaint-intelligence/0.1 (research project)"


def sha256_file(path: Path, *, chunk_bytes: int = 1024 * 1024) -> str:
    """Calculate a file's SHA-256 digest without loading it into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        while chunk := file_handle.read(chunk_bytes):
            digest.update(chunk)
    return digest.hexdigest()


def available_disk_bytes(destination: Path) -> int:
    """Return free bytes on the volume containing the destination."""
    existing_parent = destination.parent
    while not existing_parent.exists():
        existing_parent = existing_parent.parent
    return shutil.disk_usage(existing_parent).free


def validate_free_space(
    destination: Path,
    *,
    expected_bytes: int,
    minimum_multiplier: int,
) -> int:
    """Require room for the ZIP, temporary file, and later extraction."""
    if expected_bytes <= 0:
        raise ValueError("expected_bytes must be positive")
    if minimum_multiplier < 2:
        raise ValueError("minimum_multiplier must be at least 2")

    free_bytes = available_disk_bytes(destination)
    required_bytes = expected_bytes * minimum_multiplier
    if free_bytes < required_bytes:
        raise OSError(
            "Insufficient disk space for the configured archive workflow: "
            f"required at least {required_bytes:,} bytes, found {free_bytes:,} bytes"
        )
    return free_bytes


def validate_member_name(member_name: str) -> None:
    """Reject archive member paths that could escape an extraction directory."""
    normalized = member_name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe archive member path: {member_name!r}")
    if path.parts and ":" in path.parts[0]:
        raise ValueError(f"Unsafe drive-qualified archive member path: {member_name!r}")


def inspect_zip(path: Path) -> list[dict[str, Any]]:
    """Validate the ZIP and describe members without extracting them."""
    if not zipfile.is_zipfile(path):
        raise ValueError(f"Downloaded file is not a valid ZIP archive: {path}")

    members: list[dict[str, Any]] = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            validate_member_name(info.filename)
            members.append(
                {
                    "filename": info.filename,
                    "compressed_bytes": info.compress_size,
                    "uncompressed_bytes": info.file_size,
                    "crc32": f"{info.CRC:08x}",
                    "is_directory": info.is_dir(),
                }
            )

        corrupt_member = archive.testzip()
        if corrupt_member is not None:
            raise ValueError(f"ZIP integrity check failed for member: {corrupt_member}")

    if not members:
        raise ValueError("ZIP archive contains no members")
    return members


def stream_response_to_file(
    response: BinaryIO,
    temporary_path: Path,
    *,
    chunk_bytes: int,
) -> int:
    """Write a response incrementally and return the downloaded byte count."""
    if chunk_bytes <= 0:
        raise ValueError("chunk_bytes must be positive")

    downloaded = 0
    with temporary_path.open("wb") as destination:
        while chunk := response.read(chunk_bytes):
            destination.write(chunk)
            downloaded += len(chunk)
    return downloaded


def acquire_archive(
    config: dict[str, Any],
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Download, verify, inspect, and document the configured CFPB archive."""
    source = config["source"]
    local = config["local"]
    download = config["download"]
    archive_path = Path(local["archive_path"])
    metadata_path = Path(local["metadata_path"])
    temporary_path = archive_path.with_suffix(archive_path.suffix + ".part")
    expected_bytes = int(source["expected_compressed_bytes"])

    if archive_path.exists() and not overwrite:
        raise FileExistsError(
            f"Archive already exists: {archive_path}. "
            "Verify it or use --overwrite deliberately."
        )
    if metadata_path.exists() and not overwrite:
        raise FileExistsError(
            f"Metadata already exists: {metadata_path}. "
            "Refusing to replace snapshot evidence silently."
        )

    free_bytes = validate_free_space(
        archive_path,
        expected_bytes=expected_bytes,
        minimum_multiplier=int(download["minimum_free_space_multiplier"]),
    )
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path.unlink(missing_ok=True)

    request = Request(
        source["archive_url"],
        headers={"User-Agent": USER_AGENT, "Accept": "application/zip"},
    )

    try:
        with urlopen(request, timeout=int(download["timeout_seconds"])) as response:
            status = getattr(response, "status", None)
            content_type = response.headers.get("Content-Type", "")
            reported_length = response.headers.get("Content-Length")
            if status != 200:
                raise ValueError(f"Unexpected HTTP status: {status}")
            if "zip" not in content_type.lower():
                raise ValueError(f"Unexpected content type: {content_type!r}")
            if reported_length is not None and int(reported_length) != expected_bytes:
                raise ValueError(
                    "Server Content-Length differs from the reviewed value: "
                    f"expected {expected_bytes:,}, received {int(reported_length):,}"
                )

            downloaded_bytes = stream_response_to_file(
                response,
                temporary_path,
                chunk_bytes=int(download["chunk_bytes"]),
            )

        if downloaded_bytes != expected_bytes:
            raise ValueError(
                "Downloaded byte count differs from the reviewed value: "
                f"expected {expected_bytes:,}, received {downloaded_bytes:,}"
            )

        members = inspect_zip(temporary_path)
        digest = sha256_file(temporary_path, chunk_bytes=int(download["chunk_bytes"]))
        temporary_path.replace(archive_path)

        metadata = {
            "source_authority": source["authority"],
            "source_page": source["archive_page"],
            "archive_url": source["archive_url"],
            "archive_period": source["archive_period"],
            "downloaded_at_utc": datetime.now(UTC).isoformat(),
            "archive_filename": archive_path.name,
            "compressed_bytes": archive_path.stat().st_size,
            "sha256": digest,
            "free_bytes_before_download": free_bytes,
            "archive_members": members,
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return metadata
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download and verify the configured CFPB narrative archive"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/dataset.yaml"),
        help="Dataset acquisition configuration",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing archive and metadata after deliberate review",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    metadata = acquire_archive(load_config(args.config), overwrite=args.overwrite)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()

