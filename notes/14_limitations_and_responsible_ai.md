# Limitations and Responsible Use

## Purpose

This project analyses a public regulatory complaint dataset, but public availability does not make
every inference appropriate. This note records what the system can support, what it cannot prove,
and how each major risk is controlled.

## Intended use

The system supports retrospective exploration and human investigation of submitted CFPB
complaints. It can help an analyst:

- organise complaint narratives into known product labels;
- retrieve lexically similar historical cases;
- inspect exploratory complaint topics;
- identify persistent unusual changes in weekly topic share;
- review verified aggregate and structured evidence in Power BI.

It is not an automated decision-maker.

## Data limitations

### Selection bias

Only 318,804 of 945,532 source records contain a published narrative. Narrative publication
depends on consumer consent and CFPB processing. Complaint submission also depends on awareness,
access, and willingness to report.

Therefore, complaint counts do not estimate market prevalence or consumer-population risk.

### Time and taxonomy scope

The snapshot covers September 2023 through March 2024 and 11 product classes. Performance can
change when language, products, companies, reporting behavior, or CFPB taxonomy changes.

### Duplicate language

The source contains repeated and templated narratives. The classification split removes later
exact-text overlap with earlier splits, but near-duplicates and common templates can remain.

### Public does not mean harmless

Complaint IDs, companies, locations, dates, and issue labels can still create traceability and
reputational risk. Raw narratives and generated datasets remain excluded from Git. The PBIX omits
free-text narratives and retains only the structured fields required for investigation.

## Model limitations

### Imbalanced classification

The classifier achieves 0.8242 accuracy but 0.6938 macro F1. The `Debt or credit management`
class has substantially weaker performance than common categories. Predictions require human
review, especially for rare products.

### Retrieval proxy

Precision@5 of 0.5233 uses product agreement as a proxy. Two semantically related complaints can
have different products, and two complaints with the same product can describe unrelated issues.
Human relevance assessment is required before operational use.

### Overlapping topics

The selected clustering model has a low 0.0490 cosine silhouette. Some topics represent legal or
submission templates instead of distinct consumer problems. Topic terms describe lexical
centroids; they are not validated diagnoses.

### Unlabelled alert quality

The detector produced 11 persistent alerts, but there is no external incident label proving which
signals correspond to real operational events. Alert precision, recall, and business value are
therefore unknown.

## Misuse risks and controls

| Risk | Control |
|---|---|
| Treating complaints as population prevalence | Visible disclaimers and denominator documentation |
| Ranking companies or states by raw counts | No quality ranking; labels state that counts are exploratory context |
| Treating an alert as proof of misconduct | Alerts described as investigation signals only |
| Automating customer decisions | Lending, pricing, eligibility, and enforcement use explicitly prohibited |
| Leakage from future or outcome fields | Chronological splits, duplicate isolation, prior-only alert history, and excluded post-arrival fields |
| Exposing narrative text | Raw/generated data ignored; narratives excluded from PBIX and aggregate reports |
| Hiding rare-class failure behind accuracy | Macro F1, balanced accuracy, and per-class metrics reported |
| Overclaiming cluster meaning | Low silhouette and human-interpretation requirement reported |
| Unsupported generated summaries | RAG left unimplemented pending grounding and privacy evaluation |

## Human oversight

A reviewer must remain responsible for:

- confirming the meaning of a retrieved complaint or topic;
- checking source evidence and calculated values;
- deciding whether an alert merits investigation;
- separating correlation from causation;
- applying organisational policy, legal review, and access controls;
- documenting any operational action taken after analysis.

## Deployment gaps

The repository is a local portfolio prototype. It does not implement:

- user authentication, role-based access, or audit logging;
- encryption and key management infrastructure;
- production data-retention and deletion controls;
- scheduled ingestion, drift monitoring, or alert delivery;
- model registry, approval workflow, or rollback;
- incident response, service-level objectives, or regulatory approval;
- Power BI workspace permissions or row-level security.

These are not small polish items; they are required before institutional deployment.

## Safe interview statement

> This project demonstrates a reproducible local investigation workflow over a fixed public CFPB
> snapshot. It does not estimate market prevalence or prove misconduct. I report class imbalance,
> weak cluster separation, proxy retrieval labels, and unlabelled alert quality directly, keep raw
> narratives outside Git and Power BI, and require human review for every interpretation.

