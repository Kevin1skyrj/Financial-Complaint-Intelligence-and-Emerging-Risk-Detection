# SQL Analytics and Power BI-Ready Reporting

## Milestone outcome

This milestone creates a reproducible SQLite analytics warehouse, tested SQL views, and eight
privacy-reviewed CSV exports for Power BI. The later dashboard milestones used these outputs to
build and validate the five-page local `.pbix` documented in
[`12e_powerbi_completion_and_validation.md`](12e_powerbi_completion_and_validation.md).

Implemented command:

```powershell
$env:PYTHONPATH = "src"
python -m complaint_intelligence.analytics
```

## Why add SQL after Python?

Python performs acquisition, NLP, modelling, clustering, and signal detection. SQL exposes their
verified outputs through stable relational tables and views. This separation keeps complex model
logic out of dashboard calculations while making business aggregations inspectable and reusable.

SQLite was selected because it is built into Python, portable as one local file, and sufficient
for a single-user portfolio-scale analytical warehouse. PostgreSQL would be more appropriate for
concurrent users, permissions, scheduled ingestion, or production serving.

## Warehouse structure

```text
fact_complaint_topic
    -> one row per narrative complaint and assigned topic

fact_weekly_topic_metric
    -> one row per topic per complete monitoring week

fact_risk_alert
    -> persistent investigation signals only

dim_topic
    -> top terms and descriptive cluster metadata

fact_model_summary
    -> final test and calibration metrics

fact_model_class_metric
    -> precision, recall, F1, and support by product
```

The database contains no complaint narrative field. Complaint ID is retained for controlled
traceability and should not be treated as harmless public data.

## SQL views

| View | Responsibility |
|---|---|
| `vw_complaint_detail` | Privacy-safe complaint metadata and derived Monday week |
| `vw_topic_catalog` | Topic terms and cluster descriptors |
| `vw_weekly_topic_dashboard` | Weekly count, share, baseline, score, persistence, and severity |
| `vw_alert_dashboard` | Persistent alerts joined to topic descriptions |
| `vw_product_topic_summary` | Topic composition within each product |
| `vw_weekly_overview` | Weekly volume and alert summary |
| `vw_model_summary` | Aggregate classification and calibration metrics |
| `vw_model_class_performance` | Product-level model metrics |

Indexes support date, topic, product, and alert-week filtering.

## Reconciliation query

`sql/01_weekly_complaint_volume.sql` independently aggregates complaint-topic assignments by
Monday week and compares them with the monitoring fact table. The verified total absolute count
difference is **0**.

## Verified warehouse results

| Check | Result |
|---|---:|
| SQLite integrity | `ok` |
| Complaint rows | 318,804 |
| Unique complaint IDs | 318,804 |
| Weekly topic rows | 900 |
| Alert rows | 11 |
| Weekly alert flags | 11 |
| Assignment/monitoring count difference | 0 |
| Maximum weekly share-sum floating error | 1.67e-15 |
| Topic dimension rows | 30 |
| Product model-metric rows | 11 |

The share error is ordinary floating-point precision and is effectively zero.

## Power BI exports

The pipeline exports 318,804 complaint-detail rows, 30 topic rows, 900 weekly-topic rows, 11
alerts, 244 product-topic combinations, 30 weekly-overview rows, one model-summary row, and 11
product-performance rows.

Every export records its row count, column list, byte size, and SHA-256 in the analytics report.
All generated files remain Git-ignored.

## Recommended dashboard model

`topics` is the topic dimension and has one-to-many relationships with complaints, weekly topics,
and alerts. Fact tables should not be directly joined to each other because joining them by topic
would multiply rows and inflate measures.

Recommended pages are executive overview, topic monitoring, alert investigation, product and
geographic analysis, and model quality. Exact import steps, DAX measures, relationships, visuals,
and refresh checks are documented in `powerbi/README.md`.

## Privacy and interpretation controls

- Raw narrative text is rejected by a schema guard before persistence or export.
- Complaint identifiers remain controlled traceability fields.
- Geographic counts require minimum-count and non-prevalence caveats.
- Company counts must not become quality rankings.
- Alert severity represents statistical priority, not harm severity.
- Model metrics must display the held-out historical evaluation scope.

## Failures found during implementation

Two failures were detected and fixed during the real warehouse build:

1. SQLite's context manager committed but did not close the file, so Windows blocked atomic rename.
   The connection lifecycle now closes explicitly before publishing the database.
2. The first privacy guard treated the numeric field `narrative_complaints` as raw text because it
   matched the word `narrative`. The rule now blocks actual text-bearing names such as `narrative`,
   `complaint_narrative`, and `*_text` without rejecting an aggregate count.

Both cases were rerun through the complete validation suite.

## Limitations

- SQLite is a local analytical artifact, not a production multi-user warehouse.
- CSV imports do not provide incremental refresh or access control by themselves.
- The PBIX is a local Desktop artifact, not a published or scheduled Power BI service report.
- Refresh still requires regenerating local exports and refreshing the Desktop model.
- Complaint ID and company metadata remain sensitive operational fields.
- Dashboard usefulness has not been evaluated with actual analysts.

## Verification

- Complete automated suite: 50 tests passed.
- SQLite `PRAGMA integrity_check` returned `ok`.
- SQL weekly counts reconcile exactly with source assignments.
- Alert table counts reconcile exactly with weekly alert flags.
- Complaint IDs are unique.
- All eight exports passed the privacy-column guard.
- Database and export hashes were recorded.

## Interview defense

**Why use both Python and SQL?**

Python handles model-oriented transformations and experiments. SQL provides stable business-facing
tables, joins, aggregations, and reconciliation queries. I keep one authoritative implementation
for each result and validate the handoff between them.

**Why use a star-like model for Power BI?**

Dimensions filter facts through one-to-many relationships. Direct fact-to-fact joins can multiply
rows and silently inflate counts, so topics is used as a shared dimension.

**Is the Power BI dashboard complete?**

The five-page local PBIX and its visual QA are complete for version one. Power BI service
publication, scheduled refresh, and audience permissions are separate future deployment work.

**How did you ensure dashboard numbers are correct?**

I validated database integrity, uniqueness, alert reconciliation, weekly share totals, and an
independent SQL comparison between assignment counts and monitoring counts. The final difference
was zero.

## Completion boundary

The analytics and local Power BI milestones are complete. Optional future work includes dense
embedding comparisons, service publication with an approved audience, scheduled refresh, and a
carefully evaluated evidence-grounded summary layer.

