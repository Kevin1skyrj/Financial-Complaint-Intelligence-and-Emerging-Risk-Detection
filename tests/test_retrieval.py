from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer

from complaint_intelligence.retrieval import evaluate_index, search_index


def small_index() -> dict:
    texts = ["credit card charged fee", "mortgage payment late", "card billing dispute"]
    vectorizer = TfidfVectorizer().fit(texts)
    metadata = pd.DataFrame(
        {
            "complaint_id": ["1", "2", "3"],
            "product": ["Card", "Mortgage", "Card"],
            "narrative_hash": ["h1", "h2", "h3"],
        }
    )
    return {
        "vectorizer": vectorizer,
        "matrix": vectorizer.transform(texts).tocsr(),
        "metadata": metadata,
    }


def test_search_returns_ranked_metadata_without_narratives() -> None:
    results = search_index(small_index(), "card fee", k=2)
    assert results[0]["complaint_id"] == "1"
    assert results[0]["similarity"] >= results[1]["similarity"]
    assert "narrative" not in results[0]


def test_search_rejects_empty_query() -> None:
    with pytest.raises(ValueError, match="non-whitespace"):
        search_index(small_index(), "   ")


def test_retrieval_evaluation_is_disjoint_and_aggregate() -> None:
    index = small_index()
    test = pd.DataFrame(
        {
            "narrative": ["credit card fee", "home mortgage payment"],
            "product": ["Card", "Mortgage"],
            "narrative_hash": ["q1", "q2"],
        }
    )
    result = evaluate_index(
        index,
        test,
        text_column="narrative",
        target_column="product",
        hash_column="narrative_hash",
        k=1,
        per_class=2,
        batch_size=1,
        random_seed=42,
    )
    assert result["precision_at_k"] == 1.0
    assert result["hit_rate_at_k"] == 1.0
    assert result["cross_corpus_hash_overlap"] == 0


def test_evaluation_rejects_hash_overlap() -> None:
    index = small_index()
    test = pd.DataFrame(
        {"narrative": ["other"], "product": ["Card"], "narrative_hash": ["h1"]}
    )
    with pytest.raises(ValueError, match="overlaps"):
        evaluate_index(
            index,
            test,
            text_column="narrative",
            target_column="product",
            hash_column="narrative_hash",
            k=1,
            per_class=1,
            batch_size=1,
            random_seed=42,
        )


def test_index_artifact_can_be_serialized(tmp_path: Path) -> None:
    path = tmp_path / "index.joblib"
    joblib.dump(small_index(), path)
    loaded = joblib.load(path)
    assert loaded["matrix"].shape == (3, 9)
