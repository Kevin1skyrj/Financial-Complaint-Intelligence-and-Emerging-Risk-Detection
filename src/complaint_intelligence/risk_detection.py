"""Detect persistent weekly topic-share anomalies for human investigation."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from complaint_intelligence.acquisition import sha256_file
from complaint_intelligence.config import load_config


def aggregate_weekly_topics(
    assignments: pd.DataFrame,
    *,
    date_column: str,
    topic_column: str,
    analysis_start: str,
    analysis_end: str,
) -> pd.DataFrame:
    """Create a complete topic-by-week grid with counts and topic shares."""
    missing = sorted({date_column, topic_column} - set(assignments.columns))
    if missing:
        raise ValueError(f"Topic assignments are missing columns: {missing}")
    dates = pd.to_datetime(assignments[date_column], errors="coerce")
    if dates.isna().any():
        raise ValueError(f"Topic assignments contain {int(dates.isna().sum())} invalid dates")
    start = pd.Timestamp(analysis_start)
    end = pd.Timestamp(analysis_end)
    if start > end:
        raise ValueError("analysis_start must not be after analysis_end")
    selected = assignments.loc[dates.between(start, end, inclusive="both")].copy()
    selected["week_start"] = dates.loc[selected.index].dt.to_period("W-SUN").dt.start_time
    topics = sorted(selected[topic_column].astype(int).unique())
    weeks = pd.date_range(start=start, end=end, freq="W-MON")
    grid = pd.MultiIndex.from_product(
        [topics, weeks], names=[topic_column, "week_start"]
    ).to_frame(index=False)
    counts = (
        selected.assign(**{topic_column: selected[topic_column].astype(int)})
        .groupby([topic_column, "week_start"])
        .size()
        .rename("topic_count")
        .reset_index()
    )
    weekly = grid.merge(counts, on=[topic_column, "week_start"], how="left")
    weekly["topic_count"] = weekly["topic_count"].fillna(0).astype(int)
    totals = weekly.groupby("week_start")["topic_count"].transform("sum")
    weekly["total_complaints"] = totals.astype(int)
    weekly["topic_share"] = np.where(totals > 0, weekly["topic_count"] / totals, 0.0)
    return weekly.sort_values([topic_column, "week_start"]).reset_index(drop=True)


def score_topic_history(
    weekly: pd.DataFrame,
    *,
    topic_column: str,
    lookback_weeks: int,
    minimum_history_weeks: int,
    robust_z_threshold: float,
    minimum_weekly_count: int,
    minimum_share_increase: float,
    scale_floor: float,
    persistence_window_weeks: int,
    persistence_required_weeks: int,
) -> pd.DataFrame:
    """Score each week using prior data only and apply a persistence rule."""
    if lookback_weeks < minimum_history_weeks or minimum_history_weeks < 2:
        raise ValueError("lookback_weeks must be at least minimum_history_weeks >= 2")
    if not 1 <= persistence_required_weeks <= persistence_window_weeks:
        raise ValueError("Persistence requirement must be within its window")
    if scale_floor <= 0:
        raise ValueError("scale_floor must be positive")

    scored_groups = []
    for _, group in weekly.groupby(topic_column, sort=True):
        group = group.sort_values("week_start").copy()
        medians: list[float] = []
        scales: list[float] = []
        baseline_counts: list[float] = []
        history_sizes: list[int] = []
        scores: list[float] = []
        for position, row in enumerate(group.itertuples(index=False)):
            history = group.iloc[max(0, position - lookback_weeks) : position]
            history_sizes.append(len(history))
            if len(history) < minimum_history_weeks:
                medians.append(np.nan)
                scales.append(np.nan)
                baseline_counts.append(np.nan)
                scores.append(np.nan)
                continue
            shares = history["topic_share"].to_numpy(dtype=float)
            median = float(np.median(shares))
            mad = float(np.median(np.abs(shares - median)))
            robust_scale = max(1.4826 * mad, scale_floor)
            medians.append(median)
            scales.append(robust_scale)
            baseline_counts.append(float(history["topic_count"].mean()))
            scores.append((float(row.topic_share) - median) / robust_scale)
        group["history_weeks"] = history_sizes
        group["baseline_share_median"] = medians
        group["baseline_share_scale"] = scales
        group["baseline_count_mean"] = baseline_counts
        group["share_increase"] = group["topic_share"] - group["baseline_share_median"]
        group["robust_z_score"] = scores
        group["candidate_signal"] = (
            (group["robust_z_score"] >= robust_z_threshold)
            & (group["topic_count"] >= minimum_weekly_count)
            & (group["share_increase"] >= minimum_share_increase)
        )
        persistent_count = (
            group["candidate_signal"]
            .astype(int)
            .rolling(persistence_window_weeks, min_periods=1)
            .sum()
        )
        group["persistent_signal_count"] = persistent_count.astype(int)
        group["alert"] = group["candidate_signal"] & (
            persistent_count >= persistence_required_weeks
        )
        group["severity"] = np.select(
            [group["alert"] & (group["robust_z_score"] >= 7), group["alert"]],
            ["high", "review"],
            default="none",
        )
        scored_groups.append(group)
    return pd.concat(scored_groups, ignore_index=True)


def attach_topic_terms(
    frame: pd.DataFrame,
    clustering_report: dict[str, Any],
    *,
    topic_column: str,
    term_limit: int = 5,
) -> pd.DataFrame:
    """Attach non-sensitive centroid terms for human review."""
    terms = {
        int(topic["topic_id"]): ", ".join(topic["top_terms"][:term_limit])
        for topic in clustering_report["topics"]
    }
    result = frame.copy()
    result["topic_terms"] = result[topic_column].astype(int).map(terms)
    return result


def run_risk_detection(config: dict[str, Any], *, overwrite: bool = False) -> dict[str, Any]:
    data = config["data"]
    settings = config["monitoring"]
    weekly_path = Path(data["weekly_metrics_path"])
    alerts_path = Path(data["alerts_path"])
    report_path = Path(data["report_path"])
    existing = [path for path in (weekly_path, alerts_path, report_path) if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(f"Risk-detection outputs already exist: {existing}")

    assignments_path = Path(data["assignments_path"])
    clustering_report_path = Path(data["clustering_report_path"])
    assignments = pd.read_csv(
        assignments_path,
        usecols=[data["date_column"], data["topic_column"]],
        dtype={data["date_column"]: "string", data["topic_column"]: "int64"},
    )
    clustering_report = json.loads(clustering_report_path.read_text(encoding="utf-8"))
    weekly = aggregate_weekly_topics(
        assignments,
        date_column=data["date_column"],
        topic_column=data["topic_column"],
        analysis_start=str(settings["analysis_start"]),
        analysis_end=str(settings["analysis_end"]),
    )
    scored = score_topic_history(
        weekly,
        topic_column=data["topic_column"],
        lookback_weeks=int(settings["lookback_weeks"]),
        minimum_history_weeks=int(settings["minimum_history_weeks"]),
        robust_z_threshold=float(settings["robust_z_threshold"]),
        minimum_weekly_count=int(settings["minimum_weekly_count"]),
        minimum_share_increase=float(settings["minimum_share_increase"]),
        scale_floor=float(settings["scale_floor"]),
        persistence_window_weeks=int(settings["persistence_window_weeks"]),
        persistence_required_weeks=int(settings["persistence_required_weeks"]),
    )
    scored = attach_topic_terms(
        scored, clustering_report, topic_column=data["topic_column"]
    )
    alerts = scored.loc[scored["alert"]].copy()

    for path in (weekly_path, alerts_path, report_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(weekly_path, index=False, encoding="utf-8")
    alerts.to_csv(alerts_path, index=False, encoding="utf-8")

    peak_rows = (
        alerts.sort_values("robust_z_score", ascending=False)
        .head(10)[
            [
                data["topic_column"],
                "week_start",
                "topic_count",
                "topic_share",
                "baseline_share_median",
                "share_increase",
                "robust_z_score",
                "severity",
                "topic_terms",
            ]
        ]
        .copy()
    )
    if not peak_rows.empty:
        peak_rows["week_start"] = peak_rows["week_start"].dt.date.astype(str)
    report = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "method": "Rolling prior-only robust topic-share anomaly detection",
        "configuration": {
            key: value.isoformat() if hasattr(value, "isoformat") else value
            for key, value in settings.items()
        },
        "source": {
            "assignments_path": str(assignments_path),
            "assignments_sha256": sha256_file(assignments_path),
            "clustering_report_sha256": sha256_file(clustering_report_path),
        },
        "coverage": {
            "weeks": int(scored["week_start"].nunique()),
            "topics": int(scored[data["topic_column"]].nunique()),
            "weekly_topic_rows": len(scored),
            "candidate_signals": int(scored["candidate_signal"].sum()),
            "persistent_alerts": len(alerts),
            "alerted_topics": int(alerts[data["topic_column"]].nunique()),
        },
        "top_alerts": peak_rows.to_dict(orient="records"),
        "artifacts": {
            "weekly_metrics": {
                "path": str(weekly_path),
                "bytes": weekly_path.stat().st_size,
                "sha256": sha256_file(weekly_path),
            },
            "alerts": {
                "path": str(alerts_path),
                "bytes": alerts_path.stat().st_size,
                "sha256": sha256_file(alerts_path),
            },
        },
        "interpretation_warning": (
            "Alerts indicate persistent changes in archived complaint-topic share and require "
            "human investigation; they are not proof of harm, misconduct, or causation."
        ),
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detect emerging complaint-topic signals")
    parser.add_argument("--config", type=Path, default=Path("configs/risk_detection.yaml"))
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    print(json.dumps(run_risk_detection(load_config(args.config), overwrite=args.overwrite), indent=2))


if __name__ == "__main__":
    main()
