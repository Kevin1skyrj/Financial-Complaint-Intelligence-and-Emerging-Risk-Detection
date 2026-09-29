from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from complaint_intelligence.baseline import (
    build_pipeline,
    evaluate_predictions,
    load_split,
    majority_baseline,
)


MODEL_CONFIG = {
    "min_document_frequency": 1,
    "max_features": 100,
    "ngram_min": 1,
    "ngram_max": 2,
    "sublinear_tf": True,
    "class_weight": "balanced",
    "max_iterations": 100,
    "solver": "lbfgs",
    "random_seed": 42,
}


def test_pipeline_learns_vocabulary_only_when_fitted() -> None:
    pipeline = build_pipeline(MODEL_CONFIG, c_value=1.0)
    assert not hasattr(pipeline.named_steps["tfidf"], "vocabulary_")

    pipeline.fit(
        ["card billing dispute", "mortgage payment issue", "card charged fee", "loan payment"],
        ["Card", "Mortgage", "Card", "Mortgage"],
    )
    assert "billing" in pipeline.named_steps["tfidf"].vocabulary_


def test_evaluation_and_majority_baseline_are_complete() -> None:
    truth = pd.Series(["A", "A", "B", "B"])
    metrics = evaluate_predictions(truth, ["A", "A", "A", "B"], labels=["A", "B"])
    majority = majority_baseline(truth, truth, labels=["A", "B"])

    assert metrics["accuracy"] == 0.75
    assert metrics["macro_f1"] > 0
    assert len(metrics["confusion_matrix"]) == 2
    assert majority["predicted_label"] == "A"
    assert majority["accuracy"] == 0.5


def test_invalid_regularization_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        build_pipeline(MODEL_CONFIG, c_value=0)


def test_split_loader_rejects_empty_model_input(tmp_path: Path) -> None:
    path = tmp_path / "split.csv"
    pd.DataFrame({"narrative": [""], "product": ["Card"]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="invalid rows"):
        load_split(path, text_column="narrative", target_column="product")
