from __future__ import annotations

import pandas as pd
import pytest

from complaint_intelligence.risk_detection import (
    aggregate_weekly_topics,
    attach_topic_terms,
    score_topic_history,
)


def test_weekly_aggregation_builds_zero_filled_grid() -> None:
    assignments = pd.DataFrame(
        {
            "date_received": ["2024-01-01", "2024-01-02", "2024-01-08"],
            "topic_id": [0, 1, 0],
        }
    )
    weekly = aggregate_weekly_topics(
        assignments,
        date_column="date_received",
        topic_column="topic_id",
        analysis_start="2024-01-01",
        analysis_end="2024-01-14",
    )
    assert len(weekly) == 4
    missing = weekly.loc[
        (weekly["topic_id"] == 1) & (weekly["week_start"] == pd.Timestamp("2024-01-08"))
    ]
    assert missing.iloc[0]["topic_count"] == 0
    assert weekly.groupby("week_start")["topic_share"].sum().round(6).eq(1).all()


def test_persistent_spike_produces_alert_without_future_leakage() -> None:
    weeks = pd.date_range("2024-01-01", periods=10, freq="W-MON")
    weekly = pd.DataFrame(
        {
            "topic_id": [0] * 10,
            "week_start": weeks,
            "topic_count": [100] * 8 + [300, 320],
            "total_complaints": [1000] * 10,
            "topic_share": [0.1] * 8 + [0.3, 0.32],
        }
    )
    scored = score_topic_history(
        weekly,
        topic_column="topic_id",
        lookback_weeks=6,
        minimum_history_weeks=4,
        robust_z_threshold=3.5,
        minimum_weekly_count=50,
        minimum_share_increase=0.01,
        scale_floor=0.01,
        persistence_window_weeks=3,
        persistence_required_weeks=2,
    )
    assert not scored.iloc[8]["alert"]
    assert scored.iloc[9]["alert"]
    assert scored.iloc[8]["baseline_share_median"] == 0.1


def test_single_spike_does_not_pass_persistence() -> None:
    weeks = pd.date_range("2024-01-01", periods=8, freq="W-MON")
    weekly = pd.DataFrame(
        {
            "topic_id": [0] * 8,
            "week_start": weeks,
            "topic_count": [100] * 7 + [400],
            "total_complaints": [1000] * 8,
            "topic_share": [0.1] * 7 + [0.4],
        }
    )
    scored = score_topic_history(
        weekly,
        topic_column="topic_id",
        lookback_weeks=6,
        minimum_history_weeks=4,
        robust_z_threshold=3.5,
        minimum_weekly_count=50,
        minimum_share_increase=0.01,
        scale_floor=0.01,
        persistence_window_weeks=3,
        persistence_required_weeks=2,
    )
    assert scored["candidate_signal"].sum() == 1
    assert scored["alert"].sum() == 0


def test_invalid_persistence_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="Persistence"):
        score_topic_history(
            pd.DataFrame(),
            topic_column="topic_id",
            lookback_weeks=4,
            minimum_history_weeks=2,
            robust_z_threshold=3,
            minimum_weekly_count=10,
            minimum_share_increase=0.01,
            scale_floor=0.001,
            persistence_window_weeks=2,
            persistence_required_weeks=3,
        )


def test_topic_terms_are_attached_without_narratives() -> None:
    frame = pd.DataFrame({"topic_id": [0], "topic_count": [5]})
    report = {"topics": [{"topic_id": 0, "top_terms": ["card", "fee", "charge"]}]}
    result = attach_topic_terms(frame, report, topic_column="topic_id", term_limit=2)
    assert result.iloc[0]["topic_terms"] == "card, fee"
