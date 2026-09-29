"""Train and evaluate the first TF-IDF plus Logistic Regression baseline."""

from __future__ import annotations

import argparse
import json
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.pipeline import Pipeline

from complaint_intelligence.acquisition import sha256_file
from complaint_intelligence.config import load_config


def build_pipeline(model_config: dict[str, Any], *, c_value: float) -> Pipeline:
    """Construct an unfitted pipeline so TF-IDF can only learn from fit data."""
    if c_value <= 0:
        raise ValueError("Logistic Regression C must be positive")
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    min_df=int(model_config["min_document_frequency"]),
                    max_features=int(model_config["max_features"]),
                    ngram_range=(
                        int(model_config["ngram_min"]),
                        int(model_config["ngram_max"]),
                    ),
                    sublinear_tf=bool(model_config["sublinear_tf"]),
                    dtype=np.float32,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=float(c_value),
                    class_weight=model_config["class_weight"],
                    max_iter=int(model_config["max_iterations"]),
                    solver=model_config["solver"],
                    random_state=int(model_config["random_seed"]),
                ),
            ),
        ]
    )


def load_split(path: Path, *, text_column: str, target_column: str) -> pd.DataFrame:
    """Load a split and fail if model inputs are missing or empty."""
    if not path.exists():
        raise FileNotFoundError(f"Classification split not found: {path}")
    frame = pd.read_csv(path, dtype="string")
    missing = sorted({text_column, target_column} - set(frame.columns))
    if missing:
        raise ValueError(f"Classification split is missing columns: {missing}")
    invalid = frame[text_column].fillna("").str.strip().eq("") | frame[
        target_column
    ].fillna("").str.strip().eq("")
    if invalid.any():
        raise ValueError(f"Classification split contains {int(invalid.sum())} invalid rows")
    return frame


def evaluate_predictions(
    truth: pd.Series,
    predictions: Any,
    *,
    labels: list[str],
) -> dict[str, Any]:
    """Return overall, per-class, and confusion-matrix metrics."""
    return {
        "rows": len(truth),
        "accuracy": round(float(accuracy_score(truth, predictions)), 6),
        "balanced_accuracy": round(
            float(balanced_accuracy_score(truth, predictions)), 6
        ),
        "macro_f1": round(
            float(f1_score(truth, predictions, average="macro", zero_division=0)), 6
        ),
        "weighted_f1": round(
            float(f1_score(truth, predictions, average="weighted", zero_division=0)), 6
        ),
        "per_class": classification_report(
            truth,
            predictions,
            labels=labels,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(truth, predictions, labels=labels).tolist(),
    }


def majority_baseline(
    train_targets: pd.Series,
    evaluation_targets: pd.Series,
    *,
    labels: list[str],
) -> dict[str, Any]:
    """Evaluate the rule that always predicts the most frequent training class."""
    majority_label = str(train_targets.value_counts().idxmax())
    predictions = [majority_label] * len(evaluation_targets)
    return {
        "predicted_label": majority_label,
        **evaluate_predictions(evaluation_targets, predictions, labels=labels),
    }


def save_confusion_matrix(
    matrix: list[list[int]], labels: list[str], output_path: Path
) -> None:
    """Save a readable row-normalized final-test confusion matrix."""
    values = pd.DataFrame(matrix, index=labels, columns=labels, dtype="float64")
    normalized = values.div(values.sum(axis=1).replace(0, 1), axis=0)
    figure, axis = plt.subplots(figsize=(14, 12))
    image = axis.imshow(normalized, cmap="Blues", vmin=0, vmax=1)
    axis.set_xticks(range(len(labels)), labels=labels, rotation=75, ha="right")
    axis.set_yticks(range(len(labels)), labels=labels)
    axis.set_xlabel("Predicted product")
    axis.set_ylabel("Actual product")
    axis.set_title("Final Test Confusion Matrix (Row-normalized)")
    figure.colorbar(image, ax=axis, label="Share of actual class")
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(figure)


def train_baseline(
    config: dict[str, Any], *, overwrite: bool = False
) -> dict[str, Any]:
    """Select on validation, refit on train+validation, then evaluate test once."""
    data_config = config["data"]
    model_config = {**config["model"], "random_seed": config["project"]["random_seed"]}
    artifact_path = Path(model_config["artifact_path"])
    metrics_path = Path(model_config["metrics_path"])
    confusion_path = Path(model_config["confusion_matrix_path"])
    existing = [
        path for path in (artifact_path, metrics_path, confusion_path) if path.exists()
    ]
    if existing and not overwrite:
        raise FileExistsError(f"Baseline outputs already exist: {existing}")

    text_column = data_config["text_column"]
    target_column = data_config["target_column"]
    train = load_split(
        Path(data_config["train_path"]),
        text_column=text_column,
        target_column=target_column,
    )
    validation = load_split(
        Path(data_config["validation_path"]),
        text_column=text_column,
        target_column=target_column,
    )
    test = load_split(
        Path(data_config["test_path"]),
        text_column=text_column,
        target_column=target_column,
    )
    labels = sorted(set(train[target_column]) | set(validation[target_column]) | set(test[target_column]))

    candidate_results = []
    selected_pipeline: Pipeline | None = None
    selected_key: tuple[float, float] | None = None
    selected_c: float | None = None
    convergence_warnings: list[str] = []
    for candidate in model_config["candidates"]:
        c_value = float(candidate["c"])
        pipeline = build_pipeline(model_config, c_value=c_value)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            pipeline.fit(train[text_column], train[target_column])
        candidate_warnings = [
            str(item.message) for item in caught if issubclass(item.category, ConvergenceWarning)
        ]
        predictions = pipeline.predict(validation[text_column])
        metrics = evaluate_predictions(validation[target_column], predictions, labels=labels)
        candidate_results.append(
            {"c": c_value, "metrics": metrics, "convergence_warnings": candidate_warnings}
        )
        key = (metrics["macro_f1"], metrics["weighted_f1"])
        if selected_key is None or key > selected_key:
            selected_key = key
            selected_c = c_value
            selected_pipeline = pipeline

    if selected_pipeline is None or selected_c is None:
        raise ValueError("At least one model candidate is required")

    validation_majority = majority_baseline(
        train[target_column], validation[target_column], labels=labels
    )
    combined = pd.concat([train, validation], ignore_index=True)
    final_pipeline = build_pipeline(model_config, c_value=selected_c)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        final_pipeline.fit(combined[text_column], combined[target_column])
    convergence_warnings.extend(
        str(item.message) for item in caught if issubclass(item.category, ConvergenceWarning)
    )
    test_predictions = final_pipeline.predict(test[text_column])
    test_metrics = evaluate_predictions(test[target_column], test_predictions, labels=labels)
    test_majority = majority_baseline(
        combined[target_column], test[target_column], labels=labels
    )

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_pipeline, artifact_path)
    save_confusion_matrix(test_metrics["confusion_matrix"], labels, confusion_path)

    vectorizer = final_pipeline.named_steps["tfidf"]
    report = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "experiment": "TF-IDF plus Logistic Regression product classification",
        "selection_metric": "validation macro_f1, then weighted_f1 as tie-breaker",
        "selected_c": selected_c,
        "candidate_validation_results": candidate_results,
        "validation_majority_baseline": validation_majority,
        "final_fit_rows": len(combined),
        "final_vocabulary_size": len(vectorizer.vocabulary_),
        "test_metrics": test_metrics,
        "test_majority_baseline": test_majority,
        "labels": labels,
        "convergence_warnings": convergence_warnings,
        "artifacts": {
            "model": {
                "path": str(artifact_path),
                "bytes": artifact_path.stat().st_size,
                "sha256": sha256_file(artifact_path),
            },
            "confusion_matrix": {
                "path": str(confusion_path),
                "bytes": confusion_path.stat().st_size,
                "sha256": sha256_file(confusion_path),
            },
        },
        "evaluation_scope": (
            "Unique March 2024 narratives whose exact text was not retained in earlier splits."
        ),
    }
    metrics_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train the TF-IDF Logistic Regression baseline")
    parser.add_argument("--config", type=Path, default=Path("configs/baseline.yaml"))
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    report = train_baseline(load_config(args.config), overwrite=args.overwrite)
    summary = {
        "selected_c": report["selected_c"],
        "validation_candidates": [
            {"c": item["c"], "macro_f1": item["metrics"]["macro_f1"]}
            for item in report["candidate_validation_results"]
        ],
        "test_metrics": {
            key: report["test_metrics"][key]
            for key in ("accuracy", "balanced_accuracy", "macro_f1", "weighted_f1")
        },
        "model_artifact": report["artifacts"]["model"],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
