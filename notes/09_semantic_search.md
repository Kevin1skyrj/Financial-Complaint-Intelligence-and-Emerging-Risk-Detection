# Similar-Complaint Retrieval Baseline

## Milestone outcome

This milestone implements a searchable similar-complaint index over the historical training and
validation corpus. It uses cosine similarity in the fitted TF-IDF space and evaluates retrieval
on held-out March complaints.

The implementation is intentionally described as a **lexical similarity baseline**, not a neural
semantic search system. TF-IDF can match shared words and phrases but does not reliably understand
paraphrases with different vocabulary.

Build and evaluate the index:

```powershell
$env:PYTHONPATH = "src"
python -m complaint_intelligence.retrieval
```

Search the existing index:

```powershell
$env:PYTHONPATH = "src"
python -m complaint_intelligence.retrieval --query "unauthorized card charge" --k 5
```

Search results return complaint ID, date, product, narrative hash, rank, and similarity score.
They do not return stored complaint narrative text.

## Business purpose

Classification answers, "Which known product category is most likely?" Retrieval answers a
different question: "Which earlier complaints use the most similar language?"

An analyst could use retrieved cases to:

- locate related historical complaints;
- compare how similar complaints were categorized;
- investigate repeated operational patterns;
- gather evidence before interpreting a new theme;
- support a later evidence-grounded summarization workflow.

Retrieval is decision support. Similarity is not proof that two consumers experienced the same
event or that a company did something wrong.

## Index design

The index reuses the TF-IDF vectorizer fitted during the final classification training. The
historical corpus consists of the combined train and validation splits:

| Property | Verified value |
|---|---:|
| Historical complaints | 177,475 |
| TF-IDF dimensions | 50,000 |
| Non-zero sparse values | 37,310,306 |
| Serialized index size | 207,617,146 bytes |

Each document vector is L2-normalized by `TfidfVectorizer`. Its dot product with a normalized
query vector is therefore cosine similarity.

The serialized index stores:

- the fitted TF-IDF vectorizer;
- the sparse document matrix;
- complaint ID, date, product, and narrative hash metadata;
- the source-model hash and creation time.

It deliberately excludes narrative strings. The original ignored dataset remains the controlled
source when an authorized local workflow needs to inspect the full record.

## Retrieval flow

```text
query text
   -> fitted TF-IDF vectorizer
   -> sparse query vector
   -> cosine similarity against historical matrix
   -> top-k ranking
   -> non-text complaint metadata
```

No product label is used to rank results. Product is used only after retrieval as an evaluation
proxy.

## Leakage protection

The search corpus contains only September 2023 through February 2024 records. Evaluation queries
come from the March 2024 test split. The pipeline verifies that no exact narrative hash overlaps
between the evaluation queries and historical corpus.

Verified overlap: **0**.

## Evaluation design

There is no human-authored pairwise relevance dataset in this project. The current evaluation
therefore asks whether retrieved complaints share the query's CFPB product label.

To prevent the dominant credit-reporting class from controlling the average, the evaluation uses
100 deterministic test queries from each of the 11 product classes: 1,100 queries total.

Metrics at `k=5`:

- **Precision@5:** fraction of five retrieved cases sharing the query product;
- **Hit rate@5:** fraction of queries with at least one same-product result;
- **Mean reciprocal rank:** rewards a same-product result appearing near rank one;
- **Random agreement reference:** expected product match from random corpus selection.

## Verified results

| Metric | Result |
|---|---:|
| Precision@5 | 0.5233 |
| Hit rate@5 | 0.7645 |
| Mean reciprocal rank | 0.6246 |
| Random product-agreement reference | 0.0909 |
| Precision lift over random | 5.756x |

The equal number of queries per product makes the random-reference average approximately 1/11.
The retrieval baseline substantially exceeds that reference, but product agreement is still only
a proxy for actual semantic usefulness.

## Per-class findings

| Product | Precision@5 | Hit rate@5 | MRR |
|---|---:|---:|---:|
| Credit reporting or other personal consumer reports | 0.894 | 0.990 | 0.938 |
| Student loan | 0.698 | 0.890 | 0.759 |
| Mortgage | 0.684 | 0.890 | 0.781 |
| Prepaid card | 0.664 | 0.830 | 0.736 |
| Checking or savings account | 0.562 | 0.860 | 0.675 |
| Debt collection | 0.532 | 0.820 | 0.671 |
| Credit card | 0.526 | 0.880 | 0.647 |
| Vehicle loan or lease | 0.454 | 0.730 | 0.607 |
| Money transfer, virtual currency, or money service | 0.444 | 0.770 | 0.551 |
| Payday, title, personal, or advance loan | 0.234 | 0.560 | 0.389 |
| Debt or credit management | 0.064 | 0.190 | 0.118 |

The smallest and linguistically broad `Debt or credit management` class is again the weakest.
The strong credit-reporting result is partly helped by its large historical corpus and repeated
domain-specific vocabulary.

## Why this is not yet neural semantic search

TF-IDF gives zero direct similarity to synonyms that share no fitted terms. For example, two
complaints can describe the same situation using different wording and receive a weak score.
A sentence-transformer embedding can represent contextual meaning more effectively, and an ANN
index such as FAISS or HNSW can accelerate dense-vector search.

Those libraries and model weights are not currently installed. Adding them should be a measured
upgrade with the same frozen query set, latency/memory reporting, and preferably human relevance
judgements. It would be dishonest to call the present system transformer-based.

## Limitations

- Product equality is not the same as case-level relevance.
- The evaluation has no human relevance annotations.
- TF-IDF is lexical and weak on paraphrases and synonyms.
- A brute-force sparse cosine scan grows linearly with corpus size.
- Index metadata still contains identifiers and must remain access-controlled.
- The query API returns historical labels for investigation, not automated decision-making.

## Verification

- Complete automated suite: 36 tests passed.
- The full index was serialized and reloaded successfully.
- 1,100 balanced held-out queries were evaluated.
- Exact hash overlap with the historical corpus was asserted as zero.
- The report contains aggregates and no narrative strings.
- Index size and SHA-256 are recorded for reproducibility.

## Interview defense

**Why reuse the classifier's TF-IDF vectorizer?**

It is already fitted only on the approved historical corpus, has a bounded 50,000-feature space,
and provides a reproducible baseline without downloading another model. Reuse also keeps the
classification and retrieval representations consistent for the first experiment.

**Is this really semantic search?**

It is a similar-complaint retrieval baseline using lexical TF-IDF cosine similarity. I would call
it semantic search only after evaluating contextual embeddings. The architecture supports that
upgrade, but the current evidence does not justify claiming it is implemented.

**Why not use accuracy?**

Retrieval returns a ranked list rather than one class. Precision@k measures how many top results
match the proxy, hit rate checks whether at least one useful candidate appears, and reciprocal
rank rewards relevant results near the top.

**What is the next improvement?**

Create a small manually judged query-document relevance set, then compare this baseline with a
sentence-transformer plus ANN index on relevance, latency, index size, and memory.

