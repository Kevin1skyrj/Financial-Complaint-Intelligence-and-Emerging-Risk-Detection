from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from complaint_intelligence.evaluation import calibration_summary, top_confusions


def test_calibration_summary_reports_probability_quality() -> None:
    truth = pd.Series(["A", "B", "A", "B"])
    probabilities = np.array(
        [[0.9, 0.1], [0.2, 0.8], [0.6, 0.4], [0.7, 0.3]], dtype=float
    )
    result = calibration_summary(truth, probabilities, ["A", "B"], bins=5)

    assert result["multiclass_log_loss"] > 0
    assert result["multiclass_brier_score"] > 0
    assert 0 <= result["expected_calibration_error"] <= 1
    assert sum(row["count"] for row in result["bins"]) == 4


def test_calibration_rejects_wrong_probability_shape() -> None:
    with pytest.raises(ValueError, match="shape"):
        calibration_summary(pd.Series(["A"]), np.array([[1.0]]), ["A", "B"])


def test_top_confusions_excludes_correct_predictions_and_sorts() -> None:
    matrix = [[8, 2, 0], [3, 5, 1], [0, 4, 6]]
    result = top_confusions(matrix, ["A", "B", "C"], limit=3)

    assert result[0] == {
        "actual": "C",
        "predicted": "B",
        "count": 4,
        "share_of_actual_pct": 40.0,
    }
    assert all(item["actual"] != item["predicted"] for item in result)
