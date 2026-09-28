from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from complaint_intelligence.inspection import (
    inspect_text_format,
    load_snapshot_metadata,
    safe_extract_member,
    scan_csv_schema,
    verify_archive_against_metadata,
)


COLUMNS = [
    "Complaint ID",
    "Date received",
    "Product",
    "Issue",
    "Consumer complaint narrative",
]


def write_complaint_csv(path: Path) -> None:
    pd.DataFrame(
        [
            ["1", "09/01/2023", "Credit card", "Billing dispute", "Charged twice"],
            ["2", "09/08/2023", "Mortgage", "Payment issue", "Payment not posted"],
            ["3", "bad-date", "Credit card", "Billing dispute", "   "],
        ],
        columns=COLUMNS,
    ).to_csv(path, index=False, encoding="utf-8-sig")


def create_archive(tmp_path: Path) -> tuple[Path, Path]:
    csv_path = tmp_path / "complaints.csv"
    archive_path = tmp_path / "archive.zip"
    write_complaint_csv(csv_path)
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(csv_path, arcname="complaints.csv")
    return archive_path, csv_path


def test_archive_identity_is_verified(tmp_path: Path) -> None:
    archive_path, _ = create_archive(tmp_path)
    metadata = {
        "archive_filename": archive_path.name,
        "compressed_bytes": archive_path.stat().st_size,
        "sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "archive_members": [],
    }

    verify_archive_against_metadata(archive_path, metadata)

    metadata["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="SHA-256"):
        verify_archive_against_metadata(archive_path, metadata)


def test_safe_extract_member_and_format_inspection(tmp_path: Path) -> None:
    archive_path, _ = create_archive(tmp_path)
    output_path = tmp_path / "extracted" / "complaints.csv"

    result = safe_extract_member(
        archive_path,
        member_name="complaints.csv",
        output_path=output_path,
    )
    format_report = inspect_text_format(
        output_path, encoding="utf-8-sig", configured_delimiter=","
    )

    assert result["extracted_bytes"] == output_path.stat().st_size
    assert len(result["sha256"]) == 64
    assert format_report["columns"] == COLUMNS
    assert format_report["first_row_matches_header_width"] is True


def test_existing_extracted_file_is_not_overwritten(tmp_path: Path) -> None:
    archive_path, _ = create_archive(tmp_path)
    output_path = tmp_path / "complaints.csv"
    output_path.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        safe_extract_member(
            archive_path,
            member_name="complaints.csv",
            output_path=output_path,
        )


def test_schema_scan_reports_dates_labels_and_empty_text(tmp_path: Path) -> None:
    path = tmp_path / "complaints.csv"
    write_complaint_csv(path)

    report = scan_csv_schema(
        path,
        encoding="utf-8-sig",
        delimiter=",",
        chunk_rows=2,
        required_columns=COLUMNS,
    )

    assert report["rows"] == 3
    assert report["chunks"] == 2
    assert report["earliest_date"] == "2023-09-01"
    assert report["latest_date"] == "2023-09-08"
    assert report["invalid_or_missing_dates"] == 1
    assert report["empty_or_missing_narratives"] == 1
    assert report["unique_products"] == 2
    assert report["duplicate_complaint_ids"] == 0


def test_schema_scan_rejects_missing_required_column(tmp_path: Path) -> None:
    path = tmp_path / "complaints.csv"
    pd.DataFrame({"Complaint ID": ["1"]}).to_csv(path, index=False)

    with pytest.raises(ValueError, match="missing required columns"):
        scan_csv_schema(
            path,
            encoding="utf-8",
            delimiter=",",
            chunk_rows=10,
            required_columns=COLUMNS,
        )


def test_snapshot_metadata_requires_expected_keys(tmp_path: Path) -> None:
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps({"sha256": "abc"}), encoding="utf-8")

    with pytest.raises(ValueError, match="missing keys"):
        load_snapshot_metadata(path)

