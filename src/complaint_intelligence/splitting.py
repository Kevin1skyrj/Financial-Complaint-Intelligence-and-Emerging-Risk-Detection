"""Build chronological, exact-duplicate-safe classification splits."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from complaint_intelligence.acquisition import sha256_file
from complaint_intelligence.config import load_config

SPLIT_NAMES = ("train", "validation", "test")


def narrative_hash(value: str) -> str:
    """Hash text after the same conservative outer-whitespace trim used in EDA."""
    return hashlib.sha256(value.strip().encode("utf-8")).hexdigest()


def _parse_boundary(value: Any, name: str) -> pd.Timestamp:
    parsed = pd.to_datetime(str(value), errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"Invalid split boundary {name}: {value}")
    return parsed.normalize()


def validate_boundaries(split_config: dict[str, Any]) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    """Parse split windows and reject overlap or reversed ranges."""
    windows = {
        name: (
            _parse_boundary(split_config[f"{name}_start"], f"{name}_start"),
            _parse_boundary(split_config[f"{name}_end"], f"{name}_end"),
        )
        for name in SPLIT_NAMES
    }
    for name, (start, end) in windows.items():
        if start > end:
            raise ValueError(f"{name} split starts after it ends")
    if not (
        windows["train"][1] < windows["validation"][0]
        and windows["validation"][1] < windows["test"][0]
    ):
        raise ValueError("Split windows must be ordered and non-overlapping")
    return windows


def _clean_split(
    frame: pd.DataFrame,
    *,
    target_column: str,
    seen_hashes: set[str],
) -> tuple[pd.DataFrame, dict[str, int]]:
    before = len(frame)
    prior_overlap = frame["narrative_hash"].isin(seen_hashes)
    after_overlap = frame.loc[~prior_overlap].copy()

    label_counts = after_overlap.groupby("narrative_hash")[target_column].nunique()
    conflicting_hashes = set(label_counts[label_counts > 1].index)
    conflict_mask = after_overlap["narrative_hash"].isin(conflicting_hashes)
    after_conflicts = after_overlap.loc[~conflict_mask].copy()

    after_conflicts = after_conflicts.sort_values(
        ["_parsed_date", "narrative_hash"], kind="stable"
    )
    result = after_conflicts.drop_duplicates("narrative_hash", keep="first").copy()
    seen_hashes.update(result["narrative_hash"])
    return result, {
        "window_rows": before,
        "rows_removed_seen_in_earlier_split": int(prior_overlap.sum()),
        "conflicting_label_hashes_removed": len(conflicting_hashes),
        "rows_removed_for_conflicting_labels": int(conflict_mask.sum()),
        "same_label_duplicate_rows_removed": len(after_conflicts) - len(result),
        "final_rows": len(result),
    }


def build_classification_splits(
    source_path: Path,
    output_directory: Path,
    *,
    report_path: Path,
    text_column: str,
    target_column: str,
    date_column: str,
    id_column: str,
    split_config: dict[str, Any],
    overwrite: bool = False,
) -> dict[str, Any]:
    """Create unique-text temporal splits without fitting any text transformer."""
    if not source_path.exists():
        raise FileNotFoundError(f"Prepared narrative dataset not found: {source_path}")
    windows = validate_boundaries(split_config)
    output_paths = {name: output_directory / f"{name}.csv" for name in SPLIT_NAMES}
    existing = [path for path in [*output_paths.values(), report_path] if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(f"Split outputs already exist: {existing}")

    frame = pd.read_csv(source_path, dtype="string")
    required = {text_column, target_column, date_column, id_column}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Prepared dataset is missing split columns: {missing}")

    text = frame[text_column].fillna("").str.strip()
    target = frame[target_column].fillna("").str.strip()
    parsed_dates = pd.to_datetime(frame[date_column], errors="coerce")
    valid = text.ne("") & target.ne("") & parsed_dates.notna()
    working = frame.loc[valid].copy()
    working[text_column] = text.loc[valid]
    working[target_column] = target.loc[valid]
    working["_parsed_date"] = parsed_dates.loc[valid]
    working["narrative_hash"] = working[text_column].map(narrative_hash)

    assigned_mask = pd.Series(False, index=working.index)
    split_frames: dict[str, pd.DataFrame] = {}
    split_stats: dict[str, Any] = {}
    seen_hashes: set[str] = set()
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    for name in SPLIT_NAMES:
        start, end = windows[name]
        mask = working["_parsed_date"].between(start, end, inclusive="both")
        assigned_mask |= mask
        cleaned, stats = _clean_split(
            working.loc[mask], target_column=target_column, seen_hashes=seen_hashes
        )
        cleaned["split"] = name
        split_frames[name] = cleaned.drop(columns="_parsed_date")
        split_stats[name] = {
            "start": start.date().isoformat(),
            "end": end.date().isoformat(),
            **stats,
            "target_distribution": cleaned[target_column].value_counts().to_dict(),
        }

    hash_sets = {
        name: set(split_frames[name]["narrative_hash"]) for name in SPLIT_NAMES
    }
    if any(
        hash_sets[left] & hash_sets[right]
        for left, right in (("train", "validation"), ("train", "test"), ("validation", "test"))
    ):
        raise RuntimeError("Narrative hash overlap remains across splits")

    temporary_paths: list[Path] = []
    try:
        artifact_report = {}
        for name, output_path in output_paths.items():
            temporary = output_path.with_suffix(output_path.suffix + ".part")
            temporary.unlink(missing_ok=True)
            split_frames[name].to_csv(temporary, index=False, encoding="utf-8")
            temporary_paths.append(temporary)
            temporary.replace(output_path)
            artifact_report[name] = {
                "path": str(output_path),
                "bytes": output_path.stat().st_size,
                "sha256": sha256_file(output_path),
            }

        report = {
            "created_at_utc": datetime.now(UTC).isoformat(),
            "source_path": str(source_path),
            "source_bytes": source_path.stat().st_size,
            "source_sha256": sha256_file(source_path),
            "input_rows": len(frame),
            "invalid_input_rows": int((~valid).sum()),
            "valid_rows_outside_configured_windows": int((~assigned_mask).sum()),
            "strategy": (
                "Strict chronological windows; later-window hashes seen in an earlier split "
                "are removed; conflicting-label hashes and within-split exact repeats are removed."
            ),
            "text_policy": (
                "Only outer whitespace is trimmed. TF-IDF must be fit on train.csv only "
                "inside the later model pipeline."
            ),
            "splits": split_stats,
            "artifacts": artifact_report,
            "cross_split_hash_overlap": 0,
            "privacy_note": "The JSON report contains no complaint narrative text.",
        }
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
    except Exception:
        for temporary in temporary_paths:
            temporary.unlink(missing_ok=True)
        raise


def run_splitting(config: dict[str, Any], *, overwrite: bool = False) -> dict[str, Any]:
    data = config["data"]
    return build_classification_splits(
        Path(data["prepared_path"]),
        Path(data["processed_directory"]),
        report_path=Path(data["split_report_path"]),
        text_column=data["text_column"],
        target_column=data["target_column"],
        date_column=data["date_column"],
        id_column=data["id_column"],
        split_config=config["split"],
        overwrite=overwrite,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build leakage-safe temporal dataset splits")
    parser.add_argument("--config", type=Path, default=Path("configs/baseline.yaml"))
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    print(json.dumps(run_splitting(load_config(args.config), overwrite=args.overwrite), indent=2))


if __name__ == "__main__":
    main()
