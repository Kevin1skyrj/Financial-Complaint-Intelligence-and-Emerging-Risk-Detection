"""Create a narrative-only dataset and privacy-safe exploratory report."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from complaint_intelligence.acquisition import sha256_file
from complaint_intelligence.config import load_config


SOURCE_TO_OUTPUT = {
    "Complaint ID": "complaint_id",
    "Date received": "date_received",
    "Product": "product",
    "Sub-product": "sub_product",
    "Issue": "issue",
    "Sub-issue": "sub_issue",
    "Consumer complaint narrative": "narrative",
    "Company": "company",
    "State": "state",
    "Submitted via": "submitted_via",
}


def _increment(counter: Counter[str], values: pd.Series) -> None:
    counter.update(values.dropna().astype(str))


def _quantiles(values: list[int]) -> dict[str, float]:
    if not values:
        return {}
    levels = [0, 0.25, 0.5, 0.75, 0.95, 0.99, 1]
    return {
        f"p{int(level * 100):02d}": round(float(np.quantile(values, level)), 2)
        for level in levels
    }


def _coverage(total: Counter[str], available: Counter[str]) -> list[dict[str, Any]]:
    rows = []
    for label, total_count in total.most_common():
        available_count = available[label]
        rows.append(
            {
                "label": label,
                "total_complaints": total_count,
                "narrative_complaints": available_count,
                "narrative_rate_pct": round(100 * available_count / total_count, 2),
            }
        )
    return rows


def prepare_narratives(
    source_path: Path,
    output_path: Path,
    *,
    report_path: Path,
    encoding: str,
    delimiter: str,
    chunk_rows: int,
    output_columns: list[str],
    overwrite: bool = False,
) -> dict[str, Any]:
    """Filter usable narratives in chunks and write aggregate, non-text EDA."""
    if chunk_rows <= 0:
        raise ValueError("chunk_rows must be positive")
    if not source_path.exists():
        raise FileNotFoundError(f"Extracted source not found: {source_path}")
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Prepared dataset already exists: {output_path}")
    if report_path.exists() and not overwrite:
        raise FileExistsError(f"EDA report already exists: {report_path}")

    unknown_outputs = sorted(set(output_columns) - set(SOURCE_TO_OUTPUT.values()))
    if unknown_outputs:
        raise ValueError(f"Unknown configured output columns: {unknown_outputs}")

    source_columns = list(SOURCE_TO_OUTPUT)
    available_columns = pd.read_csv(
        source_path, encoding=encoding, sep=delimiter, nrows=0
    ).columns.tolist()
    missing = sorted(set(source_columns) - set(available_columns))
    if missing:
        raise ValueError(f"Source CSV is missing preparation columns: {missing}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".part")
    temporary_path.unlink(missing_ok=True)

    total_rows = 0
    usable_rows = 0
    missing_narrative_rows = 0
    invalid_date_rows = 0
    missing_product_rows = 0
    missing_issue_rows = 0
    product_total: Counter[str] = Counter()
    product_narrative: Counter[str] = Counter()
    issue_total: Counter[str] = Counter()
    issue_narrative: Counter[str] = Counter()
    weekly_total: Counter[str] = Counter()
    weekly_narrative: Counter[str] = Counter()
    monthly_narrative: Counter[str] = Counter()
    narrative_hashes: Counter[str] = Counter()
    character_lengths: list[int] = []
    word_lengths: list[int] = []
    wrote_header = False

    try:
        for chunk in pd.read_csv(
            source_path,
            encoding=encoding,
            sep=delimiter,
            dtype="string",
            usecols=source_columns,
            chunksize=chunk_rows,
            on_bad_lines="error",
        ):
            total_rows += len(chunk)
            dates = pd.to_datetime(chunk["Date received"], errors="coerce", format="mixed")
            narratives = chunk["Consumer complaint narrative"].fillna("").str.strip()
            has_narrative = narratives.ne("")

            missing_narrative_rows += int((~has_narrative).sum())
            invalid_date_rows += int(dates.isna().sum())
            missing_product_rows += int(chunk["Product"].fillna("").str.strip().eq("").sum())
            missing_issue_rows += int(chunk["Issue"].fillna("").str.strip().eq("").sum())
            _increment(product_total, chunk["Product"])
            _increment(issue_total, chunk["Issue"])

            valid_dates = dates.dropna()
            weekly_total.update(valid_dates.dt.to_period("W-SUN").astype(str))

            selected = chunk.loc[has_narrative].copy()
            selected_dates = dates.loc[has_narrative]
            selected["Consumer complaint narrative"] = narratives.loc[has_narrative]
            usable_rows += len(selected)
            _increment(product_narrative, selected["Product"])
            _increment(issue_narrative, selected["Issue"])

            valid_selected_dates = selected_dates.dropna()
            weekly_narrative.update(valid_selected_dates.dt.to_period("W-SUN").astype(str))
            monthly_narrative.update(valid_selected_dates.dt.to_period("M").astype(str))

            text = selected["Consumer complaint narrative"]
            character_lengths.extend(text.str.len().astype(int).tolist())
            word_lengths.extend(text.str.split().str.len().astype(int).tolist())
            narrative_hashes.update(
                text.map(lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest())
            )

            prepared = selected.rename(columns=SOURCE_TO_OUTPUT)
            prepared["date_received"] = selected_dates.dt.strftime("%Y-%m-%d")
            prepared.loc[selected_dates.isna(), "date_received"] = pd.NA
            prepared[output_columns].to_csv(
                temporary_path,
                mode="a",
                header=not wrote_header,
                index=False,
                encoding="utf-8",
            )
            wrote_header = True

        if not wrote_header:
            pd.DataFrame(columns=output_columns).to_csv(temporary_path, index=False)
        temporary_path.replace(output_path)

        duplicate_groups = sum(count > 1 for count in narrative_hashes.values())
        rows_in_duplicate_groups = sum(
            count for count in narrative_hashes.values() if count > 1
        )
        report = {
            "created_at_utc": datetime.now(UTC).isoformat(),
            "source_path": str(source_path),
            "output_path": str(output_path),
            "output_artifact": {
                "bytes": output_path.stat().st_size,
                "sha256": sha256_file(output_path),
                "columns": output_columns,
            },
            "filtering_funnel": {
                "source_rows": total_rows,
                "rows_without_usable_narrative": missing_narrative_rows,
                "narrative_rows_written": usable_rows,
                "narrative_retention_pct": round(100 * usable_rows / total_rows, 2)
                if total_rows
                else 0.0,
            },
            "quality": {
                "invalid_or_missing_dates_in_source": invalid_date_rows,
                "missing_or_blank_products_in_source": missing_product_rows,
                "missing_or_blank_issues_in_source": missing_issue_rows,
                "unique_narrative_hashes": len(narrative_hashes),
                "exact_duplicate_narrative_groups": duplicate_groups,
                "rows_in_exact_duplicate_groups": rows_in_duplicate_groups,
                "redundant_exact_duplicate_rows": usable_rows - len(narrative_hashes),
            },
            "narrative_length": {
                "characters": _quantiles(character_lengths),
                "words": _quantiles(word_lengths),
            },
            "product_narrative_coverage": _coverage(product_total, product_narrative),
            "issue_narrative_coverage": _coverage(issue_total, issue_narrative),
            "weekly_volume": [
                {
                    "week": week,
                    "total_complaints": weekly_total[week],
                    "narrative_complaints": weekly_narrative[week],
                }
                for week in sorted(weekly_total)
            ],
            "monthly_narrative_volume": dict(sorted(monthly_narrative.items())),
            "privacy_note": "The report contains counts and lengths, never complaint text.",
            "interpretation_warning": (
                "Complaint and narrative counts reflect database records and publication "
                "selection, not population prevalence or institution quality."
            ),
        }
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def run_preparation(config: dict[str, Any], *, overwrite: bool = False) -> dict[str, Any]:
    local = config["local"]
    extraction = config["extraction"]
    preparation = config["preparation"]
    return prepare_narratives(
        Path(local["extracted_path"]),
        Path(local["narrative_dataset_path"]),
        report_path=Path(local["eda_report_path"]),
        encoding=extraction["encoding"],
        delimiter=extraction["delimiter"],
        chunk_rows=int(preparation["chunk_rows"]),
        output_columns=list(preparation["output_columns"]),
        overwrite=overwrite,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare narrative complaints and EDA")
    parser.add_argument("--config", type=Path, default=Path("configs/dataset.yaml"))
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    print(json.dumps(run_preparation(load_config(args.config), overwrite=args.overwrite), indent=2))


if __name__ == "__main__":
    main()
