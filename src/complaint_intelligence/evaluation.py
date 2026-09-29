"""Evaluate the frozen baseline without exposing complaint narratives."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss

from complaint_intelligence.acquisition import sha256_file
from complaint_intelligence.baseline import evaluate_predictions, load_split
from complaint_intelligence.config import load_config


def calibration_summary(
    truth: pd.Series,
    probabilities: np.ndarray,
    classes: list[str],
    *,
    bins: int = 10,
) -> dict[str, Any]:
    """Calculate multiclass confidence calibration and proper scoring rules."""
    if bins <= 0:
        raise ValueError("Calibration bins must be positive")
    if probabilities.shape != (len(truth), len(classes)):
        raise ValueError("Probability matrix shape does not match truth and classes")
    confidence = probabilities.max(axis=1)
    predicted_indices = probabilities.argmax(axis=1)
    predicted = np.asarray(classes)[predicted_indices]
    correct = predicted == truth.astype(str).to_numpy()
    edges = np.linspace(0, 1, bins + 1)
    bin_rows = []
    expected_calibration_error = 0.0
    for index in range(bins):
        lower, upper = edges[index], edges[index + 1]
        mask = (confidence >= lower) & (
            (confidence <= upper) if index == bins - 1 else (confidence < upper)
        )
        count = int(mask.sum())
        mean_confidence = float(confidence[mask].mean()) if count else None
        accuracy = float(correct[mask].mean()) if count else None
        if count:
            expected_calibration_error += (count / len(truth)) * abs(
                accuracy - mean_confidence
            )
        bin_rows.append(
            {
                "lower": round(float(lower), 2),
                "upper": round(float(upper), 2),
                "count": count,
                "mean_confidence": round(mean_confidence, 6)
                if mean_confidence is not None
                else None,
                "accuracy": round(accuracy, 6) if accuracy is not None else None,
            }
        )

    class_to_index = {label: index for index, label in enumerate(classes)}
    truth_indices = truth.astype(str).map(class_to_index).to_numpy()
    one_hot = np.zeros_like(probabilities)
    one_hot[np.arange(len(truth)), truth_indices] = 1
    return {
        "expected_calibration_error": round(float(expected_calibration_error), 6),
        "multiclass_log_loss": round(
            float(log_loss(truth, probabilities, labels=classes)), 6
        ),
        "multiclass_brier_score": round(
            float(np.mean(np.sum((probabilities - one_hot) ** 2, axis=1))), 6
        ),
        "mean_confidence": round(float(confidence.mean()), 6),
        "mean_confidence_correct": round(float(confidence[correct].mean()), 6),
        "mean_confidence_incorrect": round(float(confidence[~correct].mean()), 6),
        "bins": bin_rows,
    }


def top_confusions(
    matrix: list[list[int]], labels: list[str], *, limit: int = 15
) -> list[dict[str, Any]]:
    """Return the largest off-diagonal confusion counts without complaint text."""
    rows = []
    for actual_index, actual in enumerate(labels):
        actual_total = sum(matrix[actual_index])
        for predicted_index, predicted in enumerate(labels):
            if actual_index == predicted_index:
                continue
            count = int(matrix[actual_index][predicted_index])
            if count:
                rows.append(
                    {
                        "actual": actual,
                        "predicted": predicted,
                        "count": count,
                        "share_of_actual_pct": round(100 * count / actual_total, 2),
                    }
                )
    return sorted(rows, key=lambda item: item["count"], reverse=True)[:limit]


def save_calibration_plot(summary: dict[str, Any], output_path: Path) -> None:
    populated = [row for row in summary["bins"] if row["count"]]
    figure, axis = plt.subplots(figsize=(7, 6))
    axis.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect calibration")
    axis.plot(
        [row["mean_confidence"] for row in populated],
        [row["accuracy"] for row in populated],
        marker="o",
        label="Baseline model",
    )
    axis.set(xlabel="Mean predicted confidence", ylabel="Observed accuracy")
    axis.set_title("Final Test Reliability Diagram")
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(figure)


def evaluate_saved_model(config: dict[str, Any], *, overwrite: bool = False) -> dict[str, Any]:
    """Run aggregate error and calibration analysis on the frozen test split."""
    data_config = config["data"]
    model_config = config["model"]
    model_path = Path(model_config["artifact_path"])
    report_path = Path(model_config["evaluation_report_path"])
    plot_path = Path(model_config["calibration_plot_path"])
    if not model_path.exists():
        raise FileNotFoundError(f"Trained model not found: {model_path}")
    existing = [path for path in (report_path, plot_path) if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(f"Evaluation outputs already exist: {existing}")

    test = load_split(
        Path(data_config["test_path"]),
        text_column=data_config["text_column"],
        target_column=data_config["target_column"],
    )
    model = joblib.load(model_path)
    classes = [str(label) for label in model.classes_]
    predictions = model.predict(test[data_config["text_column"]])
    probabilities = model.predict_proba(test[data_config["text_column"]])
    metrics = evaluate_predictions(
        test[data_config["target_column"]], predictions, labels=classes
    )
    calibration = calibration_summary(
        test[data_config["target_column"]], probabilities, classes
    )
    confusions = top_confusions(metrics["confusion_matrix"], classes)
    save_calibration_plot(calibration, plot_path)

    report = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "model_sha256": sha256_file(model_path),
        "test_path": data_config["test_path"],
        "test_sha256": sha256_file(Path(data_config["test_path"])),
        "metrics": metrics,
        "calibration": calibration,
        "top_confusions": confusions,
        "calibration_plot": {
            "path": str(plot_path),
            "bytes": plot_path.stat().st_size,
            "sha256": sha256_file(plot_path),
        },
        "privacy_note": (
            "Error analysis is aggregate-only; complaint narratives and individual predictions "
            "are not written to the report."
        ),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate the frozen baseline model")
    parser.add_argument("--config", type=Path, default=Path("configs/baseline.yaml"))
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    report = evaluate_saved_model(load_config(args.config), overwrite=args.overwrite)
    print(
        json.dumps(
            {
                "metrics": {
                    key: report["metrics"][key]
                    for key in ("accuracy", "balanced_accuracy", "macro_f1", "weighted_f1")
                },
                "calibration": {
                    key: report["calibration"][key]
                    for key in (
                        "expected_calibration_error",
                        "multiclass_log_loss",
                        "multiclass_brier_score",
                    )
                },
                "top_confusions": report["top_confusions"][:5],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
