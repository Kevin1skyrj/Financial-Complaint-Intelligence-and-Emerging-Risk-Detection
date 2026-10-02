# Power BI Completion, Privacy Review, and Final Validation

## Milestone outcome

The local `powerbi/Financial_Complaint_Intelligence.pbix` is complete for the version-one project
scope. The report contains five pages, uses the eight curated analytics exports, and was saved and
visually checked in Power BI Desktop on 2 October 2026.

This is a local report artifact. It has not been published to the Power BI service or shared through
`Publish to web`.

## Completed report pages

### 1. Complaint Overview

- weekly narrative-complaint volume for the 30 complete monitoring weeks;
- cards for 318,804 imported narrative complaints, 315,623 monitored complaints, 11 persistent
  alerts, and 7 alerted topics;
- persistent alerts split into 3 `high` and 8 `review` priorities;
- visible responsible-use and denominator guidance.

### 2. Emerging Risk Alerts

- alert evidence table with week, topic, severity, count, observed share, historical median,
  increase, robust z-score, persistence, and topic terms;
- complaint metadata table filtered by the selected alert's exact topic and week;
- no complaint narrative text;
- verified reconciliation of 389 supporting rows for topic 18 on 6 November 2023.

### 3. Topic Monitoring

- single-topic selector and topic descriptor;
- weekly topic share compared with its prior-history rolling median;
- evidence table containing counts, scores, persistence, severity, and shares;
- interaction checked with more than one topic.

### 4. Product & Geography

- narrative complaint counts by product;
- narrative complaint counts by state;
- issue-level complaint table sorted by volume;
- a visible interpretation note stating that counts are not population prevalence, consumer-harm
  estimates, institution-quality rankings, or causal evidence.

### 5. Model Quality

- held-out accuracy, balanced accuracy, macro F1, and expected calibration error;
- per-product precision, recall, and F1 comparison;
- evaluation scope, majority-reference macro F1, model name, and multiclass Brier score;
- test-scope text explaining that exact narrative duplicates from earlier splits were excluded.

## Verified model values shown by the report source

| Metric | Value |
|---|---:|
| Accuracy | 0.8242 |
| Balanced accuracy | 0.7578 |
| Macro F1 | 0.6938 |
| Weighted F1 | 0.8318 |
| Expected calibration error | 0.0660 |
| Majority-reference accuracy | 0.6227 |
| Majority-reference macro F1 | 0.0698 |
| Held-out test rows | 36,871 |

The majority reference demonstrates why accuracy alone is insufficient: predicting the dominant
class can obtain 0.6227 accuracy while producing only 0.0698 macro F1.

## Privacy and repository review

The eight imported tables are:

1. `complaints`
2. `topics`
3. `weekly_topics`
4. `alerts`
5. `product_topics`
6. `weekly_overview`
7. `model_summary`
8. `model_class_performance`

The report contains public CFPB complaint IDs, dates, product and issue labels, companies, states,
submission channels, derived topic IDs, aggregate topic statistics, alerts, and aggregate model
metrics. It deliberately excludes the consumer's free-text complaint narrative.

This makes the PBIX suitable for the public portfolio scope selected for this project, but it does
not make the report anonymous. Complaint IDs and company metadata remain traceability fields and
must not be used to rank institutions or identify individuals. The raw archive, prepared narrative
dataset, model artifacts, SQL database, and generated CSV exports remain Git-ignored.

## Final validation performed

- all five report tabs opened successfully after the final save;
- the report title bar confirmed a final save at 12:33 PM on 2 October 2026;
- the Downloads source and repository PBIX had the identical SHA-256
  `E69805AD0A926183C423B87148670697F8642EC3726AE0907259CD224A621AA1`;
- the report used the verified eight-table model and no narrative-bearing source table;
- page titles, labels, disclaimers, tables, charts, and main interactions were visually inspected;
- publication and public sharing were intentionally not performed.

## Interview defense

**Why is this an investigation dashboard rather than a risk-scoring dashboard?**

The alerts measure persistent changes in complaint-topic share within an archived CFPB sample.
They do not estimate customer harm, causation, misconduct, or an institution's risk level. The
dashboard exposes evidence for human review instead of turning the signal into an automated
decision.

**Why exclude narratives from Power BI?**

The business questions on these pages can be answered with structured metadata, topic assignments,
and aggregates. Excluding narrative text reduces privacy exposure while preserving traceability to
the public complaint ID for controlled follow-up.

**Why show macro F1 and balanced accuracy beside accuracy?**

The product distribution is strongly imbalanced. Accuracy is dominated by common classes, whereas
macro F1 gives every product equal influence and balanced accuracy averages recall across classes.

**Why is the report not published online?**

Creating and validating a local PBIX is separate from granting public access. Public publication
requires an explicit audience decision and a second review of the embedded data and service
permissions.

## Completion boundary

Version one is complete through the local Power BI reporting layer. Dense neural embeddings,
production APIs, scheduled refresh, Power BI service publication, and evidence-grounded generative
summaries are future extensions, not current implementation claims.
