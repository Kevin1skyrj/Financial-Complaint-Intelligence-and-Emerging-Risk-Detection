from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from complaint_intelligence.preparation import prepare_narratives


COLUMNS = [
    "Complaint ID",
    "Date received",
    "Product",
    "Sub-product",
    "Issue",
    "Sub-issue",
    "Consumer complaint narrative",
    "Company",
    "State",
    "Submitted via",
]
OUTPUT_COLUMNS = [
    "complaint_id",
    "date_received",
    "product",
    "sub_product",
    "issue",
    "sub_issue",
    "narrative",
    "company",
    "state",
    "submitted_via",
]


def write_source(path: Path) -> None:
    pd.DataFrame(
        [
            [
                "1", "09/01/2023", "Card", "General", "Billing", "Fee",
                " Charged twice ", "A", "CA", "Web",
            ],
            [
                "2", "09/08/2023", "Card", "General", "Billing", "Fee",
                "Charged twice", "A", "CA", "Web",
            ],
            [
                "3", "bad-date", "Mortgage", "Home", "Payment", None,
                "Payment missing", "B", "NY", "Phone",
            ],
            [
                "4", "09/15/2023", "Mortgage", "Home", "Payment", None,
                "   ", "B", "NY", "Web",
            ],
        ],
        columns=COLUMNS,
    ).to_csv(path, index=False)


def test_preparation_filters_text_and_reports_aggregates(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    output = tmp_path / "interim" / "narratives.csv"
    report_path = tmp_path / "interim" / "report.json"
    write_source(source)

    report = prepare_narratives(
        source,
        output,
        report_path=report_path,
        encoding="utf-8",
        delimiter=",",
        chunk_rows=2,
        output_columns=OUTPUT_COLUMNS,
    )
    prepared = pd.read_csv(output, dtype="string")

    assert prepared["complaint_id"].tolist() == ["1", "2", "3"]
    assert prepared.loc[0, "narrative"] == "Charged twice"
    assert report["filtering_funnel"]["source_rows"] == 4
    assert report["filtering_funnel"]["narrative_rows_written"] == 3
    assert report["quality"]["redundant_exact_duplicate_rows"] == 1
    assert report["quality"]["invalid_or_missing_dates_in_source"] == 1
    assert report["product_narrative_coverage"][0]["narrative_rate_pct"] == 100.0
    assert "Charged twice" not in report_path.read_text(encoding="utf-8")
    assert json.loads(report_path.read_text(encoding="utf-8")) == report


def test_preparation_refuses_silent_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    output = tmp_path / "narratives.csv"
    report = tmp_path / "report.json"
    write_source(source)
    output.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        prepare_narratives(
            source,
            output,
            report_path=report,
            encoding="utf-8",
            delimiter=",",
            chunk_rows=2,
            output_columns=OUTPUT_COLUMNS,
        )


def test_preparation_rejects_missing_source_column(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    pd.DataFrame({"Complaint ID": ["1"]}).to_csv(source, index=False)

    with pytest.raises(ValueError, match="missing preparation columns"):
        prepare_narratives(
            source,
            tmp_path / "output.csv",
            report_path=tmp_path / "report.json",
            encoding="utf-8",
            delimiter=",",
            chunk_rows=2,
            output_columns=OUTPUT_COLUMNS,
        )
