"""Discover complaint themes with a reproducible sparse clustering baseline."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics import silhouette_score

from complaint_intelligence.acquisition import sha256_file
from complaint_intelligence.config import load_config


def cluster_sizes(labels: np.ndarray, cluster_count: int) -> list[int]:
    """Return a stable size entry for every configured cluster."""
    return np.bincount(labels, minlength=cluster_count).astype(int).tolist()


def fit_candidates(
    matrix: csr_matrix,
    *,
    candidates: list[int],
    batch_size: int,
    max_iterations: int,
    n_init: int,
    sample_size: int,
    minimum_cluster_fraction: float,
    random_seed: int,
) -> tuple[MiniBatchKMeans, list[dict[str, Any]]]:
    """Fit candidate cluster counts and select by valid cosine silhouette."""
    if not candidates or any(count < 2 for count in candidates):
        raise ValueError("candidate_clusters must contain integers of at least 2")
    if not 0 <= minimum_cluster_fraction < 1:
        raise ValueError("minimum_cluster_fraction must be between 0 and 1")
    if sample_size < 2:
        raise ValueError("evaluation_sample_size must be at least 2")

    fitted: list[tuple[MiniBatchKMeans, dict[str, Any]]] = []
    for count in candidates:
        model = MiniBatchKMeans(
            n_clusters=int(count),
            random_state=random_seed,
            batch_size=batch_size,
            max_iter=max_iterations,
            n_init=n_init,
            reassignment_ratio=0.01,
        )
        labels = model.fit_predict(matrix)
        sizes = cluster_sizes(labels, count)
        silhouette = float(
            silhouette_score(
                matrix,
                labels,
                metric="cosine",
                sample_size=min(sample_size, matrix.shape[0]),
                random_state=random_seed,
            )
        )
        summary = {
            "clusters": int(count),
            "cosine_silhouette": round(silhouette, 6),
            "inertia": round(float(model.inertia_), 3),
            "minimum_cluster_rows": min(sizes),
            "maximum_cluster_rows": max(sizes),
            "minimum_cluster_fraction": round(min(sizes) / len(labels), 6),
            "empty_clusters": sum(size == 0 for size in sizes),
            "passes_size_guardrail": min(sizes) / len(labels) >= minimum_cluster_fraction,
        }
        fitted.append((model, summary))

    eligible = [item for item in fitted if item[1]["passes_size_guardrail"]]
    pool = eligible or fitted
    selected_model, _ = max(
        pool,
        key=lambda item: (
            item[1]["cosine_silhouette"],
            -item[1]["clusters"],
        ),
    )
    return selected_model, [summary for _, summary in fitted]


def extract_top_terms(
    model: MiniBatchKMeans, feature_names: np.ndarray, *, top_n: int
) -> list[dict[str, Any]]:
    """Describe centroids using their largest TF-IDF feature weights."""
    if top_n <= 0:
        raise ValueError("top_terms_per_cluster must be positive")
    topics = []
    for topic_id, centroid in enumerate(model.cluster_centers_):
        indices = np.argsort(centroid)[-top_n:][::-1]
        topics.append(
            {
                "topic_id": topic_id,
                "top_terms": [str(feature_names[index]) for index in indices],
            }
        )
    return topics


def describe_clusters(
    labels: np.ndarray,
    products: pd.Series,
    cluster_count: int,
) -> list[dict[str, Any]]:
    """Record cluster size and product mixture without treating product as topic truth."""
    frame = pd.DataFrame({"topic_id": labels, "product": products.astype(str).to_numpy()})
    descriptions = []
    for topic_id in range(cluster_count):
        subset = frame.loc[frame["topic_id"] == topic_id, "product"]
        counts = subset.value_counts()
        descriptions.append(
            {
                "topic_id": topic_id,
                "historical_rows": len(subset),
                "dominant_product": str(counts.index[0]) if len(counts) else None,
                "dominant_product_share": round(float(counts.iloc[0] / len(subset)), 6)
                if len(subset)
                else None,
                "product_count": int(counts.size),
            }
        )
    return descriptions


def assign_full_dataset(
    source_path: Path,
    output_path: Path,
    *,
    vectorizer: Any,
    model: MiniBatchKMeans,
    text_column: str,
    retained_columns: list[str],
    chunk_rows: int,
    overwrite: bool,
) -> dict[str, Any]:
    """Assign every narrative row while excluding narrative text from the output."""
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Topic assignments already exist: {output_path}")
    if chunk_rows <= 0:
        raise ValueError("assignment_chunk_rows must be positive")
    header = pd.read_csv(source_path, nrows=0).columns.tolist()
    missing = sorted(({text_column} | set(retained_columns)) - set(header))
    if missing:
        raise ValueError(f"Prepared dataset is missing clustering columns: {missing}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".part")
    temporary.unlink(missing_ok=True)
    counts: dict[int, int] = {}
    rows = 0
    wrote_header = False
    try:
        for chunk in pd.read_csv(
            source_path,
            usecols=[*retained_columns, text_column],
            dtype="string",
            chunksize=chunk_rows,
        ):
            vectors = vectorizer.transform(chunk[text_column].fillna(""))
            labels = model.predict(vectors).astype(int)
            assigned = chunk[retained_columns].copy()
            assigned["topic_id"] = labels
            assigned.to_csv(
                temporary,
                mode="a",
                header=not wrote_header,
                index=False,
                encoding="utf-8",
            )
            wrote_header = True
            rows += len(assigned)
            unique, frequencies = np.unique(labels, return_counts=True)
            for label, frequency in zip(unique, frequencies, strict=True):
                counts[int(label)] = counts.get(int(label), 0) + int(frequency)
        temporary.replace(output_path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return {
        "rows": rows,
        "topic_counts": {str(key): counts[key] for key in sorted(counts)},
        "bytes": output_path.stat().st_size,
        "sha256": sha256_file(output_path),
        "contains_narrative_text": False,
    }


def run_clustering(config: dict[str, Any], *, overwrite: bool = False) -> dict[str, Any]:
    data = config["data"]
    settings = config["clustering"]
    model_path = Path(settings["model_path"])
    report_path = Path(settings["report_path"])
    output_path = Path(data["assignments_path"])
    existing = [path for path in (model_path, report_path, output_path) if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(f"Clustering outputs already exist: {existing}")

    historical_columns = [data["text_column"], "product", "narrative_hash"]
    train = pd.read_csv(data["train_path"], usecols=historical_columns, dtype="string")
    validation = pd.read_csv(
        data["validation_path"], usecols=historical_columns, dtype="string"
    )
    historical = pd.concat([train, validation], ignore_index=True)
    if historical["narrative_hash"].duplicated().any():
        raise ValueError("Historical clustering corpus contains duplicate narrative hashes")
    stop_words: str | list[str] | None = None
    if settings["use_english_stop_words"]:
        stop_words = sorted(
            set(ENGLISH_STOP_WORDS) | set(settings.get("excluded_tokens", []))
        )
    vectorizer = TfidfVectorizer(
        min_df=int(settings["min_document_frequency"]),
        max_df=float(settings["max_document_frequency"]),
        max_features=int(settings["max_features"]),
        ngram_range=(int(settings["ngram_min"]), int(settings["ngram_max"])),
        sublinear_tf=True,
        stop_words=stop_words,
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b",
        dtype=np.float32,
    )
    matrix = vectorizer.fit_transform(historical[data["text_column"]]).tocsr()
    selected, candidates = fit_candidates(
        matrix,
        candidates=[int(value) for value in settings["candidate_clusters"]],
        batch_size=int(settings["batch_size"]),
        max_iterations=int(settings["max_iterations"]),
        n_init=int(settings["n_init"]),
        sample_size=int(settings["evaluation_sample_size"]),
        minimum_cluster_fraction=float(settings["minimum_cluster_fraction"]),
        random_seed=int(config["project"]["random_seed"]),
    )
    historical_labels = selected.labels_.astype(int)
    topics = extract_top_terms(
        selected,
        vectorizer.get_feature_names_out(),
        top_n=int(settings["top_terms_per_cluster"]),
    )
    descriptions = describe_clusters(
        historical_labels,
        historical["product"],
        selected.n_clusters,
    )
    description_by_id = {item["topic_id"]: item for item in descriptions}
    for topic in topics:
        topic.update(description_by_id[topic["topic_id"]])

    artifact = {
        "model": selected,
        "vectorizer": vectorizer,
        "topics": topics,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source_train_sha256": sha256_file(Path(data["train_path"])),
        "source_validation_sha256": sha256_file(Path(data["validation_path"])),
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_model = model_path.with_suffix(model_path.suffix + ".part")
    temporary_model.unlink(missing_ok=True)
    try:
        joblib.dump(artifact, temporary_model, compress=int(settings["artifact_compression"]))
        temporary_model.replace(model_path)
    except Exception:
        temporary_model.unlink(missing_ok=True)
        raise

    assignments = assign_full_dataset(
        Path(data["prepared_path"]),
        output_path,
        vectorizer=vectorizer,
        model=selected,
        text_column=data["text_column"],
        retained_columns=list(data["retained_columns"]),
        chunk_rows=int(settings["assignment_chunk_rows"]),
        overwrite=overwrite,
    )
    report = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "method": "TF-IDF plus MiniBatch K-Means topic-discovery baseline",
        "fit_corpus_rows": matrix.shape[0],
        "feature_count": matrix.shape[1],
        "representation": {
            "min_document_frequency": int(settings["min_document_frequency"]),
            "max_document_frequency": float(settings["max_document_frequency"]),
            "max_features": int(settings["max_features"]),
            "ngram_range": [int(settings["ngram_min"]), int(settings["ngram_max"])],
            "english_stop_words": bool(settings["use_english_stop_words"]),
            "excluded_tokens": list(settings.get("excluded_tokens", [])),
        },
        "selection_rule": (
            "Highest sampled cosine silhouette among candidates passing the minimum cluster "
            "fraction guardrail; smaller k breaks silhouette ties."
        ),
        "candidate_results": candidates,
        "selected_clusters": int(selected.n_clusters),
        "topics": topics,
        "model_artifact": {
            "path": str(model_path),
            "bytes": model_path.stat().st_size,
            "sha256": sha256_file(model_path),
        },
        "assignments": assignments,
        "interpretation_warning": (
            "Clusters are exploratory lexical groupings, not verified risk categories or proof "
            "of consumer harm. Top terms require human interpretation."
        ),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fit and evaluate complaint topic clusters")
    parser.add_argument("--config", type=Path, default=Path("configs/clustering.yaml"))
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    report = run_clustering(load_config(args.config), overwrite=args.overwrite)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
