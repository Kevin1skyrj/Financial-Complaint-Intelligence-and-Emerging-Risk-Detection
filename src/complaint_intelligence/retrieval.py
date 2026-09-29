"""Build and evaluate a privacy-conscious TF-IDF complaint retrieval index."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from complaint_intelligence.acquisition import sha256_file
from complaint_intelligence.config import load_config


def _load_columns(path: Path, columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Retrieval source split not found: {path}")
    header = pd.read_csv(path, nrows=0).columns.tolist()
    missing = sorted(set(columns) - set(header))
    if missing:
        raise ValueError(f"Retrieval source is missing columns: {missing}")
    return pd.read_csv(path, usecols=columns, dtype="string")


def build_index(
    train_path: Path,
    validation_path: Path,
    *,
    model_path: Path,
    index_path: Path,
    columns: dict[str, str],
    compression: int = 3,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Vectorize the historical corpus using the already-fitted training pipeline."""
    if index_path.exists() and not overwrite:
        raise FileExistsError(f"Retrieval index already exists: {index_path}")
    if not model_path.exists():
        raise FileNotFoundError(f"Vectorizer model not found: {model_path}")
    required = [
        columns["id"],
        columns["date"],
        columns["target"],
        columns["text"],
        columns["hash"],
    ]
    train = _load_columns(train_path, required)
    validation = _load_columns(validation_path, required)
    corpus = pd.concat([train, validation], ignore_index=True)
    if corpus[columns["hash"]].duplicated().any():
        raise ValueError("Historical retrieval corpus contains duplicate narrative hashes")

    model = joblib.load(model_path)
    vectorizer = model.named_steps["tfidf"]
    matrix = vectorizer.transform(corpus[columns["text"]]).tocsr()
    metadata = corpus.drop(columns=columns["text"]).reset_index(drop=True)
    artifact = {
        "vectorizer": vectorizer,
        "matrix": matrix,
        "metadata": metadata,
        "columns": columns,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source_model_sha256": sha256_file(model_path),
    }
    index_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = index_path.with_suffix(index_path.suffix + ".part")
    temporary.unlink(missing_ok=True)
    try:
        joblib.dump(artifact, temporary, compress=compression)
        temporary.replace(index_path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return {
        "corpus_rows": len(corpus),
        "features": matrix.shape[1],
        "nonzero_values": int(matrix.nnz),
        "index_bytes": index_path.stat().st_size,
        "index_sha256": sha256_file(index_path),
    }


def search_index(index: dict[str, Any], query: str, *, k: int = 5) -> list[dict[str, Any]]:
    """Return metadata and cosine similarity without returning stored narrative text."""
    if k <= 0:
        raise ValueError("k must be positive")
    if not query or not query.strip():
        raise ValueError("query must contain non-whitespace text")
    matrix: csr_matrix = index["matrix"]
    k = min(k, matrix.shape[0])
    query_vector = index["vectorizer"].transform([query.strip()])
    scores = (query_vector @ matrix.T).toarray().ravel()
    candidate_indices = np.argpartition(scores, -k)[-k:]
    ranked_indices = candidate_indices[np.argsort(scores[candidate_indices])[::-1]]
    metadata: pd.DataFrame = index["metadata"]
    results = []
    for rank, row_index in enumerate(ranked_indices, start=1):
        row = metadata.iloc[int(row_index)]
        result = {
            column: None if pd.isna(value) else str(value)
            for column, value in row.items()
        }
        result.update({"rank": rank, "similarity": round(float(scores[row_index]), 6)})
        results.append(result)
    return results


def _sample_queries(
    frame: pd.DataFrame,
    *,
    target_column: str,
    per_class: int,
    random_seed: int,
) -> pd.DataFrame:
    if per_class <= 0:
        raise ValueError("evaluation_queries_per_class must be positive")
    samples = []
    for _, group in frame.groupby(target_column, sort=True):
        samples.append(
            group.sample(n=min(per_class, len(group)), random_state=random_seed)
        )
    return pd.concat(samples, ignore_index=True)


def evaluate_index(
    index: dict[str, Any],
    test: pd.DataFrame,
    *,
    text_column: str,
    target_column: str,
    hash_column: str,
    k: int,
    per_class: int,
    batch_size: int,
    random_seed: int,
) -> dict[str, Any]:
    """Use product agreement as a transparent proxy for retrieval relevance."""
    if k <= 0 or batch_size <= 0:
        raise ValueError("k and batch_size must be positive")
    metadata: pd.DataFrame = index["metadata"]
    corpus_hashes = set(metadata[hash_column].dropna())
    overlap = int(test[hash_column].isin(corpus_hashes).sum())
    if overlap:
        raise ValueError(f"Test set overlaps retrieval corpus by {overlap} narrative hashes")
    queries = _sample_queries(
        test,
        target_column=target_column,
        per_class=per_class,
        random_seed=random_seed,
    )
    corpus_matrix: csr_matrix = index["matrix"]
    corpus_targets = metadata[target_column].astype(str).to_numpy()
    corpus_counts = Counter(corpus_targets)
    precision_sum = 0.0
    reciprocal_rank_sum = 0.0
    hit_count = 0
    per_class_stats: dict[str, dict[str, float]] = {}

    for start in range(0, len(queries), batch_size):
        batch = queries.iloc[start : start + batch_size]
        query_matrix = index["vectorizer"].transform(batch[text_column])
        similarities = (query_matrix @ corpus_matrix.T).toarray()
        effective_k = min(k, corpus_matrix.shape[0])
        candidates = np.argpartition(similarities, -effective_k, axis=1)[:, -effective_k:]
        for row_offset, query_target in enumerate(batch[target_column].astype(str)):
            indices = candidates[row_offset]
            ranked = indices[np.argsort(similarities[row_offset, indices])[::-1]]
            relevant = corpus_targets[ranked] == query_target
            precision = float(relevant.mean())
            hit = bool(relevant.any())
            reciprocal_rank = 1.0 / (int(np.argmax(relevant)) + 1) if hit else 0.0
            precision_sum += precision
            hit_count += int(hit)
            reciprocal_rank_sum += reciprocal_rank
            stats = per_class_stats.setdefault(
                query_target,
                {"queries": 0, "precision_sum": 0.0, "hits": 0, "rr_sum": 0.0},
            )
            stats["queries"] += 1
            stats["precision_sum"] += precision
            stats["hits"] += int(hit)
            stats["rr_sum"] += reciprocal_rank

    query_count = len(queries)
    expected_random_precision = np.mean(
        [corpus_counts[str(label)] / len(corpus_targets) for label in queries[target_column]]
    )
    return {
        "query_rows": query_count,
        "queries_per_class_limit": per_class,
        "k": k,
        "precision_at_k": round(precision_sum / query_count, 6),
        "hit_rate_at_k": round(hit_count / query_count, 6),
        "mean_reciprocal_rank": round(reciprocal_rank_sum / query_count, 6),
        "random_product_agreement_reference": round(float(expected_random_precision), 6),
        "precision_lift_over_random": round(
            (precision_sum / query_count) / expected_random_precision, 4
        ),
        "per_class": {
            label: {
                "queries": int(stats["queries"]),
                "precision_at_k": round(stats["precision_sum"] / stats["queries"], 6),
                "hit_rate_at_k": round(stats["hits"] / stats["queries"], 6),
                "mean_reciprocal_rank": round(stats["rr_sum"] / stats["queries"], 6),
            }
            for label, stats in sorted(per_class_stats.items())
        },
        "cross_corpus_hash_overlap": overlap,
        "relevance_warning": (
            "Product-label agreement is a weak evaluation proxy, not a human judgement of "
            "semantic relevance."
        ),
    }


def run_retrieval(config: dict[str, Any], *, overwrite: bool = False) -> dict[str, Any]:
    data = config["data"]
    retrieval = config["retrieval"]
    columns = {
        "id": data["id_column"],
        "date": data["date_column"],
        "target": data["target_column"],
        "text": data["text_column"],
        "hash": data["hash_column"],
    }
    index_path = Path(retrieval["index_path"])
    report_path = Path(retrieval["report_path"])
    if report_path.exists() and not overwrite:
        raise FileExistsError(f"Retrieval report already exists: {report_path}")
    index_summary = build_index(
        Path(data["train_path"]),
        Path(data["validation_path"]),
        model_path=Path(retrieval["vectorizer_model_path"]),
        index_path=index_path,
        columns=columns,
        compression=int(retrieval["artifact_compression"]),
        overwrite=overwrite,
    )
    index = joblib.load(index_path)
    test_columns = [columns[key] for key in ("id", "target", "text", "hash")]
    test = _load_columns(Path(data["test_path"]), test_columns)
    evaluation = evaluate_index(
        index,
        test,
        text_column=columns["text"],
        target_column=columns["target"],
        hash_column=columns["hash"],
        k=int(retrieval["neighbors"]),
        per_class=int(retrieval["evaluation_queries_per_class"]),
        batch_size=int(retrieval["query_batch_size"]),
        random_seed=int(config["project"]["random_seed"]),
    )
    report = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "method": "TF-IDF cosine similarity retrieval baseline",
        "index": index_summary,
        "evaluation": evaluation,
        "privacy_note": (
            "The index stores sparse vectors and metadata but no narrative strings; the report "
            "contains only aggregate retrieval metrics."
        ),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and evaluate complaint retrieval")
    parser.add_argument("--config", type=Path, default=Path("configs/retrieval.yaml"))
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--query",
        help="Search an existing index instead of rebuilding it",
    )
    parser.add_argument("--k", type=int, help="Number of results for --query")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    if args.query is not None:
        index = joblib.load(Path(config["retrieval"]["index_path"]))
        result_count = args.k or int(config["retrieval"]["neighbors"])
        print(json.dumps(search_index(index, args.query, k=result_count), indent=2))
    else:
        report = run_retrieval(config, overwrite=args.overwrite)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
