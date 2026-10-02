# Interview Defense Guide

## 30-second explanation

> I built an end-to-end financial complaint intelligence prototype on a fixed CFPB archive. It
> validates and prepares public complaint narratives, uses TF-IDF and Logistic Regression for
> product classification, retrieves similar historical cases, discovers 30 exploratory topics,
> and monitors weekly topic share for persistent unusual changes. I expose the results through a
> tested SQLite analytics layer and a five-page Power BI report. The system supports human review;
> it does not make financial decisions or treat alerts as proof of misconduct.

## Two-minute technical flow

1. I downloaded and fingerprinted an official CFPB archive containing 945,532 complaints.
2. I retained 318,804 records with public narratives and audited missingness, duplicates, class
   imbalance, length, and time coverage.
3. I created chronological train, validation, and March 2024 test windows and removed later exact
   narrative text already observed earlier.
4. I trained a class-weighted TF-IDF Logistic Regression model and evaluated 36,871 isolated test
   narratives using accuracy, balanced accuracy, macro F1, per-class metrics, calibration, and
   confusion analysis.
5. I built an exact sparse cosine-retrieval baseline and evaluated 1,100 balanced test queries.
6. I compared 12, 20, and 30-topic MiniBatch K-Means candidates with silhouette and size
   guardrails, selected 30 topics, and assigned the full narrative dataset.
7. I aggregated topic share by week and applied a prior-only median/MAD robust score plus volume,
   growth, and persistence rules, producing 11 investigation alerts across 7 topics.
8. I built validated SQLite facts, dimensions, SQL views, eight Power BI exports, and a five-page
   report with privacy and reconciliation checks.

## Headline numbers to remember

| Item | Value |
|---|---:|
| Source records | 945,532 |
| Narrative records | 318,804 |
| Held-out test narratives | 36,871 |
| Accuracy | 0.8242 |
| Balanced accuracy | 0.7578 |
| Macro F1 | 0.6938 |
| Expected calibration error | 0.0660 |
| Retrieval precision@5 | 0.5233 |
| Retrieval hit rate@5 | 0.7645 |
| Selected topics | 30 |
| Clustering silhouette | 0.0490 |
| Candidate signals | 30 |
| Persistent alerts | 11 |
| Alerted topics | 7 |
| Automated tests | 51 |

## Core questions and answers

### Why Logistic Regression instead of a transformer?

TF-IDF and Logistic Regression create a fast, reproducible, interpretable baseline that handles
high-dimensional sparse text well. A transformer should only replace it after a controlled
comparison demonstrates enough value to justify extra compute, latency, and governance.

### Why is macro F1 important here?

The largest product class dominates the dataset. Accuracy can look good while rare products fail.
Macro F1 gives each product equal weight, so it makes minority-class weakness visible.

### How did you prevent leakage?

I used chronological windows, fit learned text transformations only on approved historical data,
removed later exact-text duplicates already observed earlier, excluded post-arrival outcome fields,
and calculated each topic alert from prior weeks only.

### Why are classification, retrieval, and clustering separate?

Classification predicts a known label, retrieval ranks historical records for a query, and
clustering discovers groups without known target labels. They answer different questions and need
different evaluation methods.

### Is your retrieval really semantic search?

It is an evaluated lexical TF-IDF cosine baseline, not neural semantic search. Product agreement
is only a proxy relevance label. Dense embeddings and human relevance judgements are the next
valid comparison.

### Is a silhouette of 0.049 good?

It is low and shows substantial topic overlap. I kept the result because real complaint language
is noisy and overlapping, but I treat topics as exploratory hypotheses rather than ground truth.
The score is a limitation, not a number to hide.

### How does the alert detector work?

For each topic-week, it compares topic share with the median of up to eight previous weeks and uses
a MAD-based robust z-score. A candidate also needs minimum history, at least 100 complaints, and a
minimum share increase. An alert requires persistence in at least two of the latest three weeks.

### How do you know the 11 alerts are real risks?

I do not. They are statistically unusual persistent patterns in an archived sample. Without
verified incident labels, I cannot claim alert precision, recall, causation, or consumer harm.

### Why use Python and SQL?

Python handles data validation, modelling, and artifact generation. SQL provides stable business
facts, dimensions, joins, views, and independent reconciliation before Power BI consumes results.

### What does the Power BI report add?

It turns model and monitoring artifacts into an investigation workflow: overview KPIs, topic
history, alert evidence, supporting complaint metadata, product/geographic context, and model
quality. It excludes complaint narratives and displays interpretation limits.

### Why not publish the Power BI report immediately?

Publication changes the audience and exposure of embedded data. The local PBIX contains public
complaint IDs and structured metadata, so service permissions and audience require a separate
review. `Publish to web` would make it public and is not an ordinary sharing step.

### Why is RAG not implemented?

A language model cannot repair weak retrieval or unsupported evidence. I would first add human
relevance labels, compare dense embeddings, define a privacy-approved evidence contract, and test
citations, faithfulness, refusal, cost, and latency.

## Likely follow-up questions

1. How would you handle taxonomy changes over multiple years?
2. How would you calibrate or abstain on low-confidence predictions?
3. Which per-class errors would you prioritise and why?
4. How would you collect human relevance labels for retrieval?
5. How would you measure topic stability across seeds and time windows?
6. How would you backtest alert usefulness without leaking future information?
7. What changes are required for incremental ingestion and scheduled refresh?
8. How would role-based access and narrative redaction work in production?
9. What monitoring would detect vocabulary, label, or calibration drift?
10. Which claims are unsafe to make from CFPB complaint counts?

## Honest closing statement

> The strongest part of this project is not one headline model score. It is the traceable workflow:
> fixed data provenance, leakage controls, task-specific evaluation, explicit weak results, SQL
> reconciliation, privacy-aware reporting, automated tests, and clear separation between a local
> experiment and a production financial system.

