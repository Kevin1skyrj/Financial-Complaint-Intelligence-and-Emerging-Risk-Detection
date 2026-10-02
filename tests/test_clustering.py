from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from complaint_intelligence.clustering import (
    assign_full_dataset,
    cluster_sizes,
    extract_top_terms,
    fit_candidates,
)

TEXTS = [
    "credit card fee charge",
    "card billing charge",
    "credit card annual fee",
    "mortgage home payment",
    "home loan mortgage",
    "mortgage payment escrow",
]


def test_cluster_sizes_includes_empty_cluster() -> None:
    assert cluster_sizes(np.array([0, 0, 2]), 3) == [2, 0, 1]


def test_candidate_fit_and_top_terms() -> None:
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(TEXTS).tocsr()
    model, summaries = fit_candidates(
        matrix,
        candidates=[2],
        batch_size=3,
        max_iterations=30,
        n_init=3,
        sample_size=6,
        minimum_cluster_fraction=0,
        random_seed=42,
    )
    topics = extract_top_terms(model, vectorizer.get_feature_names_out(), top_n=3)
    assert model.n_clusters == 2
    assert len(summaries) == 1
    assert len(topics) == 2
    assert all(len(topic["top_terms"]) == 3 for topic in topics)


def test_assignment_excludes_narrative_text(tmp_path: Path) -> None:
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(TEXTS)
    model = MiniBatchKMeans(n_clusters=2, random_state=42, n_init=3).fit(matrix)
    source = tmp_path / "source.csv"
    output = tmp_path / "topics.csv"
    pd.DataFrame(
        {
            "complaint_id": ["1", "2"],
            "date_received": ["2024-01-01", "2024-01-02"],
            "product": ["Card", "Mortgage"],
            "narrative": [TEXTS[0], TEXTS[3]],
        }
    ).to_csv(source, index=False)
    result = assign_full_dataset(
        source,
        output,
        vectorizer=vectorizer,
        model=model,
        text_column="narrative",
        retained_columns=["complaint_id", "date_received", "product"],
        chunk_rows=1,
        overwrite=False,
    )
    assigned = pd.read_csv(output)
    assert result["rows"] == 2
    assert "topic_id" in assigned.columns
    assert "narrative" not in assigned.columns


def test_invalid_candidate_count_is_rejected() -> None:
    matrix = TfidfVectorizer().fit_transform(TEXTS).tocsr()
    with pytest.raises(ValueError, match="at least 2"):
        fit_candidates(
            matrix,
            candidates=[1],
            batch_size=3,
            max_iterations=10,
            n_init=1,
            sample_size=4,
            minimum_cluster_fraction=0,
            random_seed=42,
        )
