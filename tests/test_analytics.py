from __future__ import annotations

import sqlite3

import pandas as pd
import pytest

from complaint_intelligence.analytics import (
    ensure_privacy_safe_columns,
    model_metric_frames,
    topic_dimension,
    validate_database,
)


def test_topic_dimension_flattens_terms() -> None:
    report = {
        "topics": [
            {
                "topic_id": 0,
                "top_terms": ["card", "fee"],
                "historical_rows": 10,
                "dominant_product": "Card",
                "dominant_product_share": 0.8,
                "product_count": 2,
            }
        ]
    }
    result = topic_dimension(report)
    assert result.iloc[0]["top_terms"] == "card, fee"
    assert result.iloc[0]["historical_rows"] == 10


def test_model_metrics_are_flattened_for_dashboard() -> None:
    baseline = {
        "experiment": "model",
        "evaluation_scope": "held-out month",
        "test_metrics": {
            "accuracy": 0.8,
            "balanced_accuracy": 0.7,
            "macro_f1": 0.6,
            "weighted_f1": 0.75,
            "per_class": {
                "Card": {
                    "precision": 0.8,
                    "recall": 0.7,
                    "f1-score": 0.75,
                    "support": 10,
                },
                "accuracy": 0.8,
                "macro avg": {},
                "weighted avg": {},
            },
        },
        "test_majority_baseline": {"accuracy": 0.5, "macro_f1": 0.1},
    }
    evaluation = {
        "calibration": {
            "expected_calibration_error": 0.05,
            "multiclass_log_loss": 0.6,
            "multiclass_brier_score": 0.3,
        }
    }
    summary, classes = model_metric_frames(baseline, evaluation)
    assert summary.iloc[0]["macro_f1"] == 0.6
    assert classes.iloc[0]["product"] == "Card"


def test_privacy_check_rejects_narrative_column() -> None:
    with pytest.raises(ValueError, match="prohibited"):
        ensure_privacy_safe_columns(pd.DataFrame({"complaint_narrative": ["text"]}), "bad")


def test_database_validation_reconciles_tables(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "sql").mkdir()
    (tmp_path / "sql" / "01_weekly_complaint_volume.sql").write_text(
        "SELECT '2024-01-01' week_start, 0 topic_id, 2 assignment_count, "
        "2 monitoring_count, 0 count_difference",
        encoding="utf-8",
    )
    connection = sqlite3.connect(":memory:")
    pd.DataFrame({"complaint_id": ["1", "2"]}).to_sql(
        "fact_complaint_topic", connection, index=False
    )
    pd.DataFrame(
        {
            "week_start": ["2024-01-01"],
            "topic_share": [1.0],
            "alert": [1],
        }
    ).to_sql("fact_weekly_topic_metric", connection, index=False)
    pd.DataFrame({"week_start": ["2024-01-01"]}).to_sql(
        "fact_risk_alert", connection, index=False
    )
    result = validate_database(connection)
    assert result["sqlite_integrity"] == "ok"
    assert result["complaint_rows"] == 2


def test_database_validation_rejects_duplicate_ids(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "sql").mkdir()
    (tmp_path / "sql" / "01_weekly_complaint_volume.sql").write_text(
        "SELECT 0 count_difference", encoding="utf-8"
    )
    connection = sqlite3.connect(":memory:")
    pd.DataFrame({"complaint_id": ["1", "1"]}).to_sql(
        "fact_complaint_topic", connection, index=False
    )
    pd.DataFrame(
        {"week_start": ["2024-01-01"], "topic_share": [1.0], "alert": [0]}
    ).to_sql("fact_weekly_topic_metric", connection, index=False)
    pd.DataFrame({"week_start": []}).to_sql("fact_risk_alert", connection, index=False)
    with pytest.raises(ValueError, match="not unique"):
        validate_database(connection)
