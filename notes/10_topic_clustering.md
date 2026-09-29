# Topic Discovery and Cluster Evaluation

## Milestone outcome

This milestone groups complaint narratives into exploratory themes using TF-IDF and MiniBatch
K-Means. It fits topics on unique historical narratives from September 2023 through February
2024, selects a cluster count through quantitative and qualitative checks, and assigns a topic ID
to all 318,804 narrative complaints for later weekly monitoring.

Implemented command:

```powershell
$env:PYTHONPATH = "src"
python -m complaint_intelligence.clustering
```

The output assignment table excludes narrative text and retains complaint ID, date, product,
issue, company, state, submission channel, and topic ID.

## Why clustering is different from classification

Classification learns known product labels from examples. Clustering has no target label; it
groups documents based on representation similarity. The resulting clusters are hypotheses for
analyst interpretation, not automatically validated business categories.

In this project clustering supports:

- discovering repeated language patterns below broad product labels;
- creating topic-level weekly volume series;
- identifying possible emerging themes;
- guiding analysts toward groups that deserve manual review.

## Why MiniBatch K-Means?

Standard K-Means repeatedly processes the entire dataset. MiniBatch K-Means updates centroids
from smaller batches, which is more practical for 177,475 sparse historical vectors. It remains
simple, reproducible, and compatible with TF-IDF.

Trade-offs:

- the number of clusters must be selected in advance;
- initialization can affect results, so a fixed seed and multiple initializations are used;
- clusters are roughly centroid-shaped and may not match complex topic structure;
- TF-IDF groups lexical patterns rather than full contextual meaning.

## Fit corpus versus assignment corpus

The model is fit on 177,475 unique train-plus-validation narratives. This prevents repeated
templates from dominating centroid learning and keeps the March period unseen during fitting.

After fitting, the selected model assigns topics to the full 318,804-row narrative dataset.
Repetitions are preserved here because repeated complaints contribute real volume to the next
emerging-risk analysis.

## Representation designed for clustering

Classification and clustering do not require identical text representations. The first clustering
attempt reused the classifier's 50,000-feature vocabulary. That attempt failed qualitatively:

- all candidate cluster counts failed the 0.5% minimum-size guardrail;
- some clusters contained only one historical row;
- top terms were dominated by `xxxx`, `xx`, generic words, and legal boilerplate.

That failed experiment showed why silhouette alone is insufficient. The final clustering-specific
TF-IDF representation uses:

| Setting | Value |
|---|---:|
| Features | 30,000 |
| Word n-grams | 1 to 2 |
| Minimum document frequency | 10 |
| Maximum document frequency | 70% |
| English stop words | Removed |
| Redaction tokens | `xx` through `xxxxxxxx` removed |
| Term frequency | Sublinear |

Numbers and single-character tokens are excluded from clustering. The original narratives remain
unchanged in the source data.

## Choosing the number of clusters

Candidates were selected before examining the final results: 12, 20, and 30 clusters.

| Clusters | Sampled cosine silhouette | Minimum cluster rows | Maximum cluster rows | Size guardrail |
|---:|---:|---:|---:|---|
| 12 | 0.0345 | 914 | 43,388 | Pass |
| 20 | 0.0426 | 1,326 | 23,408 | Pass |
| 30 | **0.0490** | 1,018 | 24,399 | Pass |

The final guardrail requires every historical cluster to contain at least 0.2% of the fitting
corpus. All refined candidates pass. `k=30` was selected because it has the highest sampled cosine
silhouette.

The silhouette score is low in absolute terms. Real complaints overlap across products and issues,
and high-dimensional language does not form perfectly separated spherical groups. The score
supports comparison among these candidates; it does not prove that 30 objectively correct topics
exist.

## Interpreting discovered themes

Clusters have numeric IDs rather than permanent names. Top centroid terms provide evidence for a
human-readable interpretation. Examples include:

| Topic | Representative top terms | Cautious interpretation |
|---:|---|---|
| 2 | identity, identity theft, block, business days | Identity-theft reporting blocks |
| 5 | authorize, inquiry, credit report, credit inquiries | Unauthorized credit inquiries |
| 9 | debt, collection, collector, validation, contract | Debt collection and validation |
| 13 | identity theft, victim, accounts, remove | Identity-theft account removal |
| 16 | loan, student, payments, forbearance, mortgage | Loan servicing and repayment |
| 17 | card, credit card, charges, account, bank | Credit-card account and charge problems |
| 19 | bank, funds, checking, account, check | Deposit-account and funds access |
| 24 | late payments, payment history, markings | Late-payment reporting |
| 29 | inquiry, hard inquiry, date, remove | Hard-inquiry disputes |

Some clusters still represent legal templates, company-specific language, or broad mixed complaint
language. Those are valid findings about the corpus but may be less useful as operational risk
themes. Topic labels should therefore remain editable analyst annotations rather than model truth.

## Product composition is descriptive, not ground truth

The report records each cluster's dominant CFPB product and its share. Product purity can help
interpret a cluster, but the clustering algorithm never uses product labels during fitting.

A cluster spanning many products is not necessarily bad: fraud, payment failure, customer service,
and identity theft can genuinely cross product boundaries. Conversely, a product-pure cluster can
merely reflect repeated templates rather than a meaningful sub-theme.

## Generated artifacts

- `models/tfidf_minibatch_kmeans.joblib` — clustering vectorizer, model, and topic terms;
- `data/processed/topics/clustering_report.json` — candidate results and aggregate topic metadata;
- `data/processed/topics/complaint_topics.csv` — 318,804 privacy-safe topic assignments.

The assignment file is approximately 44.8 MB and contains no complaint narrative text. All
generated artifacts remain Git-ignored.

## Limitations

- The selected cosine silhouette is only 0.0490.
- K-Means requires a fixed cluster count and spherical centroid assumptions.
- TF-IDF cannot reliably group paraphrases with different vocabulary.
- Some clusters reflect legal or submission templates rather than underlying consumer problems.
- Topic IDs have no inherent ordering or permanent meaning.
- Cluster identities can change when data, vocabulary, seed, or configuration changes.
- Product composition is not a human relevance judgement.
- A human review sample is still required before operational topic naming.

## Verification

- Complete automated suite: 40 tests passed.
- Three cluster counts were fit and evaluated on the real historical corpus.
- All final candidates passed the minimum-size guardrail and had zero empty clusters.
- Model artifact serialization and full-data assignment completed successfully.
- Assignment rows equal the 318,804 source narrative rows.
- Assignment output programmatically excludes the narrative column.
- Artifact byte sizes and SHA-256 hashes are recorded.

## Interview defense

**Why did you not reuse the classifier representation unchanged?**

The initial result was dominated by stop words, redaction markers, and tiny clusters. Classification
can still use common contextual words effectively, but unsupervised centroids need cleaner
descriptive features. I recorded the failure and created a clustering-specific representation.

**Why was `k=30` selected?**

It had the highest sampled cosine silhouette among predeclared candidates, all clusters contained
at least 0.2% of the fitting corpus, and qualitative top-term inspection produced recognizable
themes. I still treat 30 as an experimental choice, not a natural truth.

**Is a silhouette of 0.049 good?**

It is low, indicating substantial overlap between clusters. High-dimensional real-world complaint
language often overlaps, but the value means these topics should be used for exploration and
monitoring—not treated as cleanly separated labels.

**Why keep duplicate rows for weekly monitoring?**

Duplicates can distort model fitting, so the centroids use unique narratives. But repeated
complaints can be an operational volume signal, so the assignment table preserves every source
row for time-series aggregation.

## Next milestone

The next milestone will aggregate topic assignments weekly, establish historical baselines, detect
unusual topic-volume changes, and apply persistence and minimum-volume rules before producing
human-review alerts.

