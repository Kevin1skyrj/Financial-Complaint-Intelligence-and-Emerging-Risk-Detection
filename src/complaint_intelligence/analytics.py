"""Build a validated SQLite analytics layer and Power BI-ready exports."""

from __future__ import annotations

import argparse
import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from complaint_intelligence.acquisition import sha256_file
from complaint_intelligence.config import load_config


PROHIBITED_COLUMN_NAMES = {"narrative", "consumer complaint narrative", "complaint_text"}


def topic_dimension(clustering_report: dict[str, Any]) -> pd.DataFrame:
    """Convert aggregate cluster descriptions into a topic dimension."""
    rows = []
    for topic in clustering_report["topics"]:
        rows.append(
            {
                "topic_id": int(topic["topic_id"]),
                "top_terms": ", ".join(topic["top_terms"]),
                "historical_rows": int(topic["historical_rows"]),
                "dominant_product": topic["dominant_product"],
                "dominant_product_share": topic["dominant_product_share"],
                "product_count": int(topic["product_count"]),
            }
        )
    return pd.DataFrame(rows).sort_values("topic_id").reset_index(drop=True)


def model_metric_frames(
    baseline_report: dict[str, Any], evaluation_report: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Flatten aggregate and per-class model metrics for dashboard use."""
    metrics = baseline_report["test_metrics"]
    majority = baseline_report["test_majority_baseline"]
    calibration = evaluation_report["calibration"]
    summary = pd.DataFrame(
        [
            {
                "model_name": baseline_report["experiment"],
                "accuracy": metrics["accuracy"],
                "balanced_accuracy": metrics["balanced_accuracy"],
                "macro_f1": metrics["macro_f1"],
                "weighted_f1": metrics["weighted_f1"],
                "majority_accuracy": majority["accuracy"],
                "majority_macro_f1": majority["macro_f1"],
                "expected_calibration_error": calibration[
                    "expected_calibration_error"
                ],
                "multiclass_log_loss": calibration["multiclass_log_loss"],
                "multiclass_brier_score": calibration["multiclass_brier_score"],
                "evaluation_scope": baseline_report["evaluation_scope"],
            }
        ]
    )
    excluded = {"accuracy", "macro avg", "weighted avg"}
    class_rows = [
        {
            "product": product,
            "precision": values["precision"],
            "recall": values["recall"],
            "f1_score": values["f1-score"],
            "support": int(values["support"]),
        }
        for product, values in metrics["per_class"].items()
        if product not in excluded
    ]
    return summary, pd.DataFrame(class_rows).sort_values("product").reset_index(drop=True)


def ensure_privacy_safe_columns(frame: pd.DataFrame, table_name: str) -> None:
    """Reject text-bearing columns before analytics persistence."""
    prohibited = []
    for column in frame.columns:
        normalized = column.lower()
        if (
            normalized in PROHIBITED_COLUMN_NAMES
            or normalized.endswith("_narrative")
            or normalized.endswith("_text")
        ):
            prohibited.append(column)
    if prohibited:
        raise ValueError(f"{table_name} contains prohibited text columns: {prohibited}")


def validate_database(connection: sqlite3.Connection) -> dict[str, Any]:
    """Run row-count, uniqueness, reconciliation, and SQLite integrity checks."""
    query = pd.read_sql_query
    integrity = query("PRAGMA integrity_check", connection).iloc[0, 0]
    complaint_rows = int(query("SELECT COUNT(*) AS n FROM fact_complaint_topic", connection).n[0])
    unique_ids = int(
        query("SELECT COUNT(DISTINCT complaint_id) AS n FROM fact_complaint_topic", connection).n[0]
    )
    weekly_rows = int(query("SELECT COUNT(*) AS n FROM fact_weekly_topic_metric", connection).n[0])
    alert_rows = int(query("SELECT COUNT(*) AS n FROM fact_risk_alert", connection).n[0])
    alert_flag_rows = int(
        query(
            "SELECT COUNT(*) AS n FROM fact_weekly_topic_metric WHERE alert = 1",
            connection,
        ).n[0]
    )
    share_error = float(
        query(
            """
            SELECT MAX(ABS(share_sum - 1.0)) AS error
            FROM (
                SELECT week_start, SUM(topic_share) AS share_sum
                FROM fact_weekly_topic_metric
                GROUP BY week_start
            )
            """,
            connection,
        ).error[0]
    )
    reconciliation = query(Path("sql/01_weekly_complaint_volume.sql").read_text(), connection)
    count_difference = int(reconciliation["count_difference"].abs().sum())
    checks = {
        "sqlite_integrity": integrity,
        "complaint_rows": complaint_rows,
        "unique_complaint_ids": unique_ids,
        "weekly_topic_rows": weekly_rows,
        "alert_rows": alert_rows,
        "weekly_alert_flag_rows": alert_flag_rows,
        "maximum_weekly_share_sum_error": share_error,
        "assignment_monitoring_count_difference": count_difference,
    }
    failures = []
    if integrity != "ok":
        failures.append("SQLite integrity check failed")
    if complaint_rows != unique_ids:
        failures.append("Complaint IDs are not unique")
    if alert_rows != alert_flag_rows:
        failures.append("Alert table does not reconcile with weekly metrics")
    if share_error > 1e-8:
        failures.append("Weekly topic shares do not sum to one")
    if count_difference != 0:
        failures.append("Weekly monitoring counts do not reconcile with assignments")
    if failures:
        raise ValueError("; ".join(failures))
    return checks


def build_analytics(config: dict[str, Any], *, overwrite: bool = False) -> dict[str, Any]:
    """Build source tables, SQL views, validations, and CSV exports."""
    data = config["data"]
    analytics = config["analytics"]
    database_path = Path(analytics["database_path"])
    report_path = Path(analytics["report_path"])
    export_directory = Path(analytics["export_directory"])
    export_paths = {
        view: export_directory / filename for view, filename in analytics["exports"].items()
    }
    existing = [
        path
        for path in [database_path, report_path, *export_paths.values()]
        if path.exists()
    ]
    if existing and not overwrite:
        raise FileExistsError(f"Analytics outputs already exist: {existing}")

    complaints = pd.read_csv(data["topic_assignments_path"], dtype="string")
    weekly = pd.read_csv(data["weekly_metrics_path"])
    alerts = pd.read_csv(data["alerts_path"])
    clustering_report = json.loads(
        Path(data["clustering_report_path"]).read_text(encoding="utf-8")
    )
    baseline_report = json.loads(
        Path(data["baseline_metrics_path"]).read_text(encoding="utf-8")
    )
    evaluation_report = json.loads(
        Path(data["evaluation_report_path"]).read_text(encoding="utf-8")
    )
    topics = topic_dimension(clustering_report)
    model_summary, model_classes = model_metric_frames(
        baseline_report, evaluation_report
    )
    for name, frame in (
        ("fact_complaint_topic", complaints),
        ("fact_weekly_topic_metric", weekly),
        ("fact_risk_alert", alerts),
        ("dim_topic", topics),
        ("fact_model_summary", model_summary),
        ("fact_model_class_metric", model_classes),
    ):
        ensure_privacy_safe_columns(frame, name)

    database_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    export_directory.mkdir(parents=True, exist_ok=True)
    temporary_database = database_path.with_suffix(database_path.suffix + ".part")
    temporary_database.unlink(missing_ok=True)
    try:
        with closing(sqlite3.connect(temporary_database)) as connection:
            with connection:
                complaints.to_sql(
                    "fact_complaint_topic", connection, index=False, if_exists="replace"
                )
                weekly.to_sql(
                    "fact_weekly_topic_metric", connection, index=False, if_exists="replace"
                )
                alerts.to_sql("fact_risk_alert", connection, index=False, if_exists="replace")
                topics.to_sql("dim_topic", connection, index=False, if_exists="replace")
                model_summary.to_sql(
                    "fact_model_summary", connection, index=False, if_exists="replace"
                )
                model_classes.to_sql(
                    "fact_model_class_metric", connection, index=False, if_exists="replace"
                )
                connection.executescript(
                    Path(analytics["schema_path"]).read_text(encoding="utf-8")
                )
                validation = validate_database(connection)
        temporary_database.replace(database_path)
    except Exception:
        temporary_database.unlink(missing_ok=True)
        raise

    exports = {}
    with closing(sqlite3.connect(database_path)) as connection:
        for view, output_path in export_paths.items():
            frame = pd.read_sql_query(f"SELECT * FROM {view}", connection)
            ensure_privacy_safe_columns(frame, view)
            frame.to_csv(output_path, index=False, encoding="utf-8")
            exports[view] = {
                "path": str(output_path),
                "rows": len(frame),
                "columns": frame.columns.tolist(),
                "bytes": output_path.stat().st_size,
                "sha256": sha256_file(output_path),
            }

    report = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "database": {
            "path": str(database_path),
            "bytes": database_path.stat().st_size,
            "sha256": sha256_file(database_path),
            "engine": "SQLite",
        },
        "source_hashes": {
            key: sha256_file(Path(path))
            for key, path in data.items()
            if key.endswith("_path")
        },
        "validation": validation,
        "exports": exports,
        "privacy_note": (
            "The warehouse and exports exclude complaint narrative text. Complaint IDs remain "
            "for traceability and should be handled as controlled record identifiers."
        ),
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build SQL analytics and Power BI exports")
    parser.add_argument("--config", type=Path, default=Path("configs/analytics.yaml"))
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    print(json.dumps(build_analytics(load_config(args.config), overwrite=args.overwrite), indent=2))


if __name__ == "__main__":
    main()
