"""Safe archive extraction and chunked schema inspection."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, BinaryIO

import pandas as pd

from complaint_intelligence.acquisition import (
    available_disk_bytes,
    sha256_file,
    validate_member_name,
)
from complaint_intelligence.config import load_config


def copy_with_sha256(
    source: BinaryIO,
    destination: Path,
    *,
    chunk_bytes: int = 1024 * 1024,
) -> tuple[int, str]:
    """Copy a binary stream while returning its byte count and SHA-256."""
    if chunk_bytes <= 0:
        raise ValueError("chunk_bytes must be positive")

    digest = hashlib.sha256()
    copied = 0
    with destination.open("wb") as output:
        while chunk := source.read(chunk_bytes):
            output.write(chunk)
            digest.update(chunk)
            copied += len(chunk)
    return copied, digest.hexdigest()


def load_snapshot_metadata(path: Path) -> dict[str, Any]:
    """Load acquisition metadata and validate its basic shape."""
    if not path.exists():
        raise FileNotFoundError(f"Snapshot metadata not found: {path}")
    metadata = json.loads(path.read_text(encoding="utf-8"))
    required = {"archive_filename", "compressed_bytes", "sha256", "archive_members"}
    missing = sorted(required - set(metadata))
    if missing:
        raise ValueError(f"Snapshot metadata is missing keys: {missing}")
    return metadata


def verify_archive_against_metadata(archive_path: Path, metadata: dict[str, Any]) -> None:
    """Reconfirm archive identity before extracting it."""
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    if archive_path.name != metadata["archive_filename"]:
        raise ValueError("Archive filename does not match snapshot metadata")
    if archive_path.stat().st_size != int(metadata["compressed_bytes"]):
        raise ValueError("Archive byte size does not match snapshot metadata")
    actual_hash = sha256_file(archive_path)
    if actual_hash != metadata["sha256"]:
        raise ValueError("Archive SHA-256 does not match snapshot metadata")


def safe_extract_member(
    archive_path: Path,
    *,
    member_name: str,
    output_path: Path,
    overwrite: bool = False,
    chunk_bytes: int = 1024 * 1024,
) -> dict[str, Any]:
    """Extract one explicitly named, validated ZIP member using a temporary file."""
    validate_member_name(member_name)
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Extracted file already exists: {output_path}. "
            "Use --overwrite only after verifying the target."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".part")
    temporary_path.unlink(missing_ok=True)

    try:
        with zipfile.ZipFile(archive_path) as archive:
            try:
                info = archive.getinfo(member_name)
            except KeyError as error:
                raise ValueError(f"Configured member is absent from archive: {member_name}") from error

            if info.is_dir():
                raise ValueError(f"Configured archive member is a directory: {member_name}")
            free_bytes = available_disk_bytes(output_path)
            required_free_bytes = info.file_size * 2
            if free_bytes < required_free_bytes:
                raise OSError(
                    "Insufficient disk space for safe extraction: "
                    f"required {required_free_bytes:,}, found {free_bytes:,} bytes"
                )

            with archive.open(info, "r") as source:
                extracted_bytes, extracted_hash = copy_with_sha256(
                    source, temporary_path, chunk_bytes=chunk_bytes
                )

        if extracted_bytes != info.file_size:
            raise ValueError(
                "Extracted byte count does not match ZIP metadata: "
                f"expected {info.file_size:,}, received {extracted_bytes:,}"
            )
        temporary_path.replace(output_path)
        return {
            "member_name": member_name,
            "extracted_path": str(output_path),
            "extracted_bytes": extracted_bytes,
            "sha256": extracted_hash,
            "crc32": f"{info.CRC:08x}",
            "extracted_at_utc": datetime.now(UTC).isoformat(),
            "free_bytes_before_extraction": free_bytes,
        }
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def inspect_text_format(path: Path, *, encoding: str, configured_delimiter: str) -> dict[str, Any]:
    """Inspect BOM, decoding, delimiter, header, and a non-sensitive sample profile."""
    if not path.exists():
        raise FileNotFoundError(f"Extracted data file not found: {path}")

    with path.open("rb") as source:
        prefix = source.read(4)
    has_utf8_bom = prefix.startswith(b"\xef\xbb\xbf")

    with path.open("r", encoding=encoding, newline="") as source:
        sample_text = source.read(65536)
    try:
        detected = csv.Sniffer().sniff(sample_text, delimiters=",\t;|")
        detected_delimiter = detected.delimiter
    except csv.Error:
        detected_delimiter = None

    with path.open("r", encoding=encoding, newline="") as source:
        reader = csv.reader(source, delimiter=configured_delimiter)
        header = next(reader)
        first_row = next(reader, None)

    if not header or len(header) == 1:
        raise ValueError("CSV header could not be parsed with the configured delimiter")
    if detected_delimiter is not None and detected_delimiter != configured_delimiter:
        raise ValueError(
            f"Detected delimiter {detected_delimiter!r} differs from configured "
            f"delimiter {configured_delimiter!r}"
        )

    first_row_width = len(first_row) if first_row is not None else 0
    return {
        "encoding_used": encoding,
        "has_utf8_bom": has_utf8_bom,
        "configured_delimiter": configured_delimiter,
        "detected_delimiter": detected_delimiter,
        "column_count": len(header),
        "columns": header,
        "first_row_field_count": first_row_width,
        "first_row_matches_header_width": first_row_width == len(header),
    }


def validate_required_columns(columns: list[str], required_columns: list[str]) -> None:
    """Fail before a full scan if the archived schema lacks required fields."""
    missing = sorted(set(required_columns) - set(columns))
    if missing:
        raise ValueError(f"Extracted CSV is missing required columns: {missing}")


def scan_csv_schema(
    path: Path,
    *,
    encoding: str,
    delimiter: str,
    chunk_rows: int,
    required_columns: list[str],
) -> dict[str, Any]:
    """Scan the CSV in chunks without persisting complaint narratives."""
    if chunk_rows <= 0:
        raise ValueError("chunk_rows must be positive")

    header = pd.read_csv(path, encoding=encoding, sep=delimiter, nrows=0).columns.tolist()
    validate_required_columns(header, required_columns)

    row_count = 0
    chunk_count = 0
    null_counts: Counter[str] = Counter()
    product_counts: Counter[str] = Counter()
    issue_counts: Counter[str] = Counter()
    seen_ids: set[str] = set()
    duplicate_complaint_ids = 0
    invalid_dates = 0
    earliest_date: pd.Timestamp | None = None
    latest_date: pd.Timestamp | None = None
    narrative_empty_or_whitespace = 0

    use_columns = list(dict.fromkeys(required_columns))
    for chunk in pd.read_csv(
        path,
        encoding=encoding,
        sep=delimiter,
        dtype="string",
        usecols=use_columns,
        chunksize=chunk_rows,
        on_bad_lines="error",
    ):
        chunk_count += 1
        row_count += len(chunk)
        null_counts.update({column: int(value) for column, value in chunk.isna().sum().items()})

        ids = chunk["Complaint ID"].dropna().astype(str)
        duplicate_complaint_ids += int(ids.duplicated().sum())
        unique_chunk_ids = set(ids.unique())
        duplicate_complaint_ids += len(unique_chunk_ids & seen_ids)
        seen_ids.update(unique_chunk_ids)

        parsed_dates = pd.to_datetime(chunk["Date received"], errors="coerce", format="mixed")
        invalid_dates += int(parsed_dates.isna().sum())
        chunk_min = parsed_dates.min()
        chunk_max = parsed_dates.max()
        if pd.notna(chunk_min):
            earliest_date = chunk_min if earliest_date is None else min(earliest_date, chunk_min)
        if pd.notna(chunk_max):
            latest_date = chunk_max if latest_date is None else max(latest_date, chunk_max)

        narratives = chunk["Consumer complaint narrative"].fillna("").str.strip()
        narrative_empty_or_whitespace += int(narratives.eq("").sum())
        product_counts.update(chunk["Product"].dropna().astype(str))
        issue_counts.update(chunk["Issue"].dropna().astype(str))

    return {
        "file_path": str(path),
        "scanned_at_utc": datetime.now(UTC).isoformat(),
        "rows": row_count,
        "chunks": chunk_count,
        "chunk_rows": chunk_rows,
        "columns": header,
        "column_count": len(header),
        "required_columns": required_columns,
        "null_counts_for_required_columns": dict(null_counts),
        "duplicate_complaint_ids": duplicate_complaint_ids,
        "unique_non_null_complaint_ids": len(seen_ids),
        "invalid_or_missing_dates": invalid_dates,
        "earliest_date": _date_string(earliest_date),
        "latest_date": _date_string(latest_date),
        "empty_or_missing_narratives": narrative_empty_or_whitespace,
        "unique_products": len(product_counts),
        "unique_issues": len(issue_counts),
        "top_products": product_counts.most_common(20),
        "top_issues": issue_counts.most_common(20),
        "scope_warning": (
            "Counts describe the selected historical archive, not the prevalence of "
            "consumer harm in the population."
        ),
    }


def extract_and_inspect(config: dict[str, Any], *, overwrite: bool = False) -> dict[str, Any]:
    """Run archive re-verification, controlled extraction, and chunked schema scanning."""
    local = config["local"]
    extraction = config["extraction"]
    archive_path = Path(local["archive_path"])
    snapshot_metadata = load_snapshot_metadata(Path(local["metadata_path"]))
    verify_archive_against_metadata(archive_path, snapshot_metadata)

    extraction_result = safe_extract_member(
        archive_path,
        member_name=extraction["member_name"],
        output_path=Path(local["extracted_path"]),
        overwrite=overwrite,
        chunk_bytes=int(config["download"]["chunk_bytes"]),
    )
    extraction_metadata_path = Path(local["extraction_metadata_path"])
    extraction_metadata_path.write_text(
        json.dumps(extraction_result, indent=2), encoding="utf-8"
    )

    format_report = inspect_text_format(
        Path(local["extracted_path"]),
        encoding=extraction["encoding"],
        configured_delimiter=extraction["delimiter"],
    )
    schema_report = scan_csv_schema(
        Path(local["extracted_path"]),
        encoding=extraction["encoding"],
        delimiter=extraction["delimiter"],
        chunk_rows=int(extraction["scan_chunk_rows"]),
        required_columns=list(extraction["required_columns"]),
    )
    report = {
        "source_archive_sha256": snapshot_metadata["sha256"],
        "extraction": extraction_result,
        "text_format": format_report,
        "schema_scan": schema_report,
    }
    report_path = Path(local["schema_report_path"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _date_string(value: pd.Timestamp | None) -> str | None:
    if value is None or pd.isna(value):
        return None
    return value.date().isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely extract and inspect the configured CFPB narrative archive"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/dataset.yaml"),
        help="Dataset configuration",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing extracted file after deliberate review",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    result = extract_and_inspect(load_config(args.config), overwrite=args.overwrite)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

