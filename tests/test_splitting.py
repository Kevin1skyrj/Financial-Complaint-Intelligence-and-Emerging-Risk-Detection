from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from complaint_intelligence.splitting import build_classification_splits, validate_boundaries


WINDOWS = {
    "train_start": "2023-09-01",
    "train_end": "2023-12-31",
    "validation_start": "2024-01-01",
    "validation_end": "2024-02-29",
    "test_start": "2024-03-01",
    "test_end": "2024-03-31",
}


def write_source(path: Path) -> None:
    pd.DataFrame(
        [
            ["1", "2023-09-01", "Card", "alpha text"],
            ["2", "2023-09-02", "Card", "alpha text"],
            ["3", "2023-10-01", "Loan", "conflicting text"],
            ["4", "2023-10-02", "Card", "conflicting text"],
            ["5", "2024-01-02", "Card", "alpha text"],
            ["6", "2024-01-03", "Loan", "validation only"],
            ["7", "2024-03-02", "Loan", "validation only"],
            ["8", "2024-03-03", "Mortgage", "test only"],
            ["9", "bad-date", "Card", "invalid date"],
            ["10", "2024-04-01", "Card", "outside window"],
        ],
        columns=["complaint_id", "date_received", "product", "narrative"],
    ).to_csv(path, index=False)


def run_split(tmp_path: Path) -> tuple[dict, Path]:
    source = tmp_path / "narratives.csv"
    output = tmp_path / "processed"
    write_source(source)
    report = build_classification_splits(
        source,
        output,
        report_path=output / "split_report.json",
        text_column="narrative",
        target_column="product",
        date_column="date_received",
        id_column="complaint_id",
        split_config=WINDOWS,
    )
    return report, output


def test_splits_are_chronological_unique_and_disjoint(tmp_path: Path) -> None:
    report, output = run_split(tmp_path)
    train = pd.read_csv(output / "train.csv", dtype="string")
    validation = pd.read_csv(output / "validation.csv", dtype="string")
    test = pd.read_csv(output / "test.csv", dtype="string")

    assert train["complaint_id"].tolist() == ["1"]
    assert validation["complaint_id"].tolist() == ["6"]
    assert test["complaint_id"].tolist() == ["8"]
    assert report["splits"]["train"]["rows_removed_for_conflicting_labels"] == 2
    assert report["splits"]["validation"]["rows_removed_seen_in_earlier_split"] == 1
    assert report["splits"]["test"]["rows_removed_seen_in_earlier_split"] == 1
    assert report["cross_split_hash_overlap"] == 0
    assert report["invalid_input_rows"] == 1
    assert report["valid_rows_outside_configured_windows"] == 1


def test_report_contains_no_narrative_text(tmp_path: Path) -> None:
    _, output = run_split(tmp_path)
    content = (output / "split_report.json").read_text(encoding="utf-8")
    assert "alpha text" not in content
    assert json.loads(content)["artifacts"]["train"]["sha256"]


def test_existing_outputs_are_not_overwritten(tmp_path: Path) -> None:
    _, output = run_split(tmp_path)
    source = tmp_path / "narratives.csv"
    with pytest.raises(FileExistsError, match="already exist"):
        build_classification_splits(
            source,
            output,
            report_path=output / "split_report.json",
            text_column="narrative",
            target_column="product",
            date_column="date_received",
            id_column="complaint_id",
            split_config=WINDOWS,
        )


def test_overlapping_windows_are_rejected() -> None:
    invalid = {**WINDOWS, "validation_start": "2023-12-01"}
    with pytest.raises(ValueError, match="ordered and non-overlapping"):
        validate_boundaries(invalid)
