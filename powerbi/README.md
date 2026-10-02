# Power BI Report

`Financial_Complaint_Intelligence.pbix` is the completed local reporting artifact for version one
of this project. It was built in Power BI Desktop from eight generated analytics tables and
contains five visually validated pages.

The report is **not** published to the Power BI service. The PBIX can be opened locally after
cloning the repository, while refresh requires regenerating the Git-ignored source exports.

## Report pages

| Page | Purpose |
|---|---|
| Complaint Overview | Monitor complaint volume, complete-week coverage, alert count, alerted topics, and severity mix |
| Emerging Risk Alerts | Inspect each persistent signal and its exact topic-week complaint metadata |
| Topic Monitoring | Compare a selected topic's weekly share with its prior-history baseline and detection evidence |
| Product & Geography | Explore product, state, and issue volumes with a non-prevalence disclaimer |
| Model Quality | Review aggregate and per-product classification performance and evaluation scope |

## Verified headline values

| Measure | Value |
|---|---:|
| Narrative complaints imported | 318,804 |
| Complaints in 30 complete monitoring weeks | 315,623 |
| Topics | 30 |
| Candidate weekly signals | 30 |
| Persistent alerts | 11 |
| Alerted topics | 7 |
| Classification accuracy | 0.8242 |
| Balanced accuracy | 0.7578 |
| Macro F1 | 0.6938 |
| Expected calibration error | 0.0660 |

## Data model

The `topics` dimension filters the main fact-like tables through one-to-many, single-direction
relationships:

```text
topics[topic_id] 1 -> * complaints[topic_id]
topics[topic_id] 1 -> * weekly_topics[topic_id]
topics[topic_id] 1 -> * alerts[topic_id]
topics[topic_id] 1 -> * product_topics[topic_id]
```

The two model-evaluation tables and `weekly_overview` remain separate because they have different
grains. Fact tables are not joined directly to each other, preventing row multiplication.

## Source tables

Run the analytics stage from the repository root:

```powershell
$env:PYTHONPATH = "src"
python -m complaint_intelligence.analytics
```

The Git-ignored sources are written to `data/processed/powerbi/`:

| File | Rows | Use |
|---|---:|---|
| `complaints.csv` | 318,804 | Structured complaint metadata and topic assignment |
| `topics.csv` | 30 | Topic terms and descriptive product context |
| `weekly_topics.csv` | 900 | Weekly count, share, baseline, score, persistence, and alert state |
| `alerts.csv` | 11 | Persistent signals for investigation |
| `product_topics.csv` | 244 | Topic composition within products |
| `weekly_overview.csv` | 30 | Complete-week volume and alert summary |
| `model_summary.csv` | 1 | Aggregate classification and calibration metrics |
| `model_class_performance.csv` | 11 | Per-product precision, recall, F1, and support |

## Important measures

```DAX
Narrative Complaints = DISTINCTCOUNT(complaints[complaint_id])

Monitored Complaints = SUM(weekly_overview[narrative_complaints])

Persistent Alerts = COUNTROWS(alerts)

Alerted Topics = DISTINCTCOUNT(alerts[topic_id])

Average Topic Share = AVERAGE(weekly_topics[topic_share])

Maximum Risk Score = MAX(weekly_topics[robust_z_score])
```

The Emerging Risk Alerts page also uses a visual-level helper measure so one selected alert filters
the lower metadata table by both topic and week. Its implementation and reconciliation are
documented in
[`../notes/12d_powerbi_alert_investigation.md`](../notes/12d_powerbi_alert_investigation.md).

## Privacy review

The PBIX embeds structured public CFPB metadata, public complaint IDs, and derived analytical
fields. It does **not** import the consumer's free-text complaint narrative.

The report is privacy-reduced, not anonymous. Complaint IDs and company names remain traceability
fields. They must not be interpreted as evidence of individual harm, company quality, misconduct,
or market prevalence. Raw data, prepared narrative text, models, the SQLite warehouse, and source
CSV exports remain excluded from Git.

## Refresh and QA checklist

Before replacing or publishing the report:

- confirm 318,804 complaint rows and unique complaint IDs;
- confirm 30 topics, 900 topic-week rows, 11 alerts, and 11 product metric rows;
- verify that weekly topic shares sum to approximately 100%;
- verify the alert table and weekly alert flags both total 11;
- confirm no imported column contains complaint narrative text;
- check all five pages for clipped titles, illegible labels, empty visuals, and misleading totals;
- test topic selection and alert-to-metadata filtering;
- retain the non-prevalence and human-review disclaimers;
- save, reopen, and check the exact PBIX before any distribution decision.

## Completion and publication boundary

The five-page Desktop report and local visual QA are complete. Power BI service publication,
scheduled refresh, workspace access, and public sharing are not configured. `Publish to web`
would create public exposure and must never be used without a separate explicit data and audience
review.

For the full final validation record, see
[`../notes/12e_powerbi_completion_and_validation.md`](../notes/12e_powerbi_completion_and_validation.md).
