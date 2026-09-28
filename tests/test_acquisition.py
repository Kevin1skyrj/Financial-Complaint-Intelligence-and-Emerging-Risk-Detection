from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from complaint_intelligence.acquisition import (
    inspect_zip,
    sha256_file,
    stream_response_to_file,
    validate_free_space,
    validate_member_name,
)


def create_zip(path: Path, member_name: str = "complaints.csv") -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member_name, "Complaint ID,Date received\n1,2024-01-01\n")


def test_sha256_file_matches_known_digest(tmp_path: Path) -> None:
    path = tmp_path / "example.bin"
    path.write_bytes(b"financial-complaints")

    assert sha256_file(path) == "0f2b5c9cd23a660b727d71abba5a07a5fde8142015aafc782b0c7e4442acdd57"


def test_stream_response_writes_incrementally(tmp_path: Path) -> None:
    destination = tmp_path / "download.part"

    count = stream_response_to_file(io.BytesIO(b"abcdefghij"), destination, chunk_bytes=3)

    assert count == 10
    assert destination.read_bytes() == b"abcdefghij"


def test_inspect_zip_returns_member_metadata(tmp_path: Path) -> None:
    path = tmp_path / "archive.zip"
    create_zip(path)

    members = inspect_zip(path)

    assert len(members) == 1
    assert members[0]["filename"] == "complaints.csv"
    assert members[0]["uncompressed_bytes"] > 0
    assert members[0]["is_directory"] is False


@pytest.mark.parametrize(
    "member_name",
    ["../outside.csv", "/absolute.csv", "folder/../../outside.csv", "C:/outside.csv"],
)
def test_unsafe_archive_members_are_rejected(member_name: str) -> None:
    with pytest.raises(ValueError, match="Unsafe"):
        validate_member_name(member_name)


def test_invalid_zip_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "not-a-zip.zip"
    path.write_text("not a zip", encoding="utf-8")

    with pytest.raises(ValueError, match="not a valid ZIP"):
        inspect_zip(path)


def test_free_space_multiplier_validation(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="minimum_multiplier"):
        validate_free_space(tmp_path / "archive.zip", expected_bytes=100, minimum_multiplier=1)

