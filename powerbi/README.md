# Power BI Dashboard Build Guide

The SQL analytics layer and Power BI-ready CSV files are implemented and verified. A `.pbix`
file has not yet been created, so the interactive dashboard must not be claimed as deployed.

## Generate the source tables

From the repository root:

```powershell
$env:PYTHONPATH = "src"
python -m complaint_intelligence.analytics
```

Power BI sources are written to `data/processed/powerbi/`:

| File | Rows | Dashboard use |
|---|---:|---|
| `complaints.csv` | 318,804 | Complaint metadata drill-through |
| `topics.csv` | 30 | Topic descriptions and dominant products |
| `weekly_topics.csv` | 900 | Topic trends, baselines, scores, and alert flags |
| `alerts.csv` | 11 | Persistent alert review table |
| `product_topics.csv` | 244 | Product-to-topic composition |
| `weekly_overview.csv` | 30 | Executive weekly volume and alert summary |
| `model_summary.csv` | 1 | Final classification and calibration metrics |
| `model_class_performance.csv` | 11 | Per-product precision, recall, and F1 |

These generated files are intentionally Git-ignored because complaint identifiers and analytical
data should not be published with the source repository.

## Import procedure

1. Open Power BI Desktop.
2. Choose **Get data -> Text/CSV**.
3. Import all eight CSV files from `data/processed/powerbi/`.
4. In Power Query, set `date_received` and `week_start` to Date.
5. Set IDs and category columns to Text or Whole Number as appropriate.
6. Set shares, scores, and model metrics to Decimal Number.
7. Set `candidate_signal` and `alert` to True/False.
8. Apply changes only after confirming the preview row counts match the table above.

## Relationships

Create these one-to-many relationships:

```text
topics[topic_id] 1 -> * complaints[topic_id]
topics[topic_id] 1 -> * weekly_topics[topic_id]
topics[topic_id] 1 -> * alerts[topic_id]
```

`product_topics` is already aggregated and can remain disconnected for its composition page, or
be connected through a separately created product dimension. Do not directly join fact tables to
each other on topic ID because that creates many-to-many duplication.

## Suggested measures

```DAX
Narrative Complaints = DISTINCTCOUNT(complaints[complaint_id])

Persistent Alerts = COUNTROWS(alerts)

Alerted Topics = DISTINCTCOUNT(alerts[topic_id])

Average Topic Share = AVERAGE(weekly_topics[topic_share])

Maximum Risk Score = MAX(weekly_topics[robust_z_score])

Macro F1 = MAX(model_summary[macro_f1])

Majority Macro F1 = MAX(model_summary[majority_macro_f1])
```

## Recommended pages

### 1. Executive overview

- cards: narrative complaints, persistent alerts, alerted topics, macro F1;
- line chart: `weekly_overview[week_start]` against `narrative_complaints`;
- column chart: alerts by week and severity;
- slicers: date, product, topic, state.

### 2. Topic monitoring

- topic selector using `topics[top_terms]`;
- line chart with weekly topic share and baseline median;
- columns for weekly topic count;
- conditional table showing robust z-score, persistence count, and severity.

The baseline line is not an alert threshold by itself; all configured conditions and persistence
must be satisfied.

### 3. Alert investigation

- sortable alert table with week, topic, terms, count, share, change, score, and severity;
- topic-to-product composition chart;
- complaint metadata drill-through filtered by topic and week.

Do not expose complaint narratives in the dashboard.

### 4. Product and geography

- product volume and topic-composition charts;
- state map only with adequate counts and a clear non-prevalence disclaimer;
- issue and submission-channel breakdowns.

Complaint counts must not be presented as institution-quality rankings or population prevalence.

### 5. Model quality

- cards for accuracy, balanced accuracy, macro F1, and calibration error;
- clustered bars for per-product precision, recall, and F1;
- comparison cards for model macro F1 versus majority-reference macro F1;
- visible evaluation-scope text from `model_summary[evaluation_scope]`.

## Refresh checks

Before publishing or taking screenshots, confirm:

- 318,804 complaint rows and unique complaint IDs;
- 900 weekly topic rows;
- 30 topic rows;
- 11 alert rows;
- weekly topic shares sum to approximately 100%;
- model-class metrics contain 11 products;
- no imported table contains complaint narrative text;
- the archive period and refresh timestamp are visible.

## Current completion boundary

Complete: SQL warehouse, views, reconciliations, CSV exports, schema, measures, and page design.

Not complete: interactive `.pbix` construction, rendered visual QA, dashboard screenshots, and
publication. Those require Power BI Desktop and a separate verified milestone.

