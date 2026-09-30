# Power BI Complaint Overview: First Interactive Dashboard Milestone

## What was built

The local `powerbi/Financial_Complaint_Intelligence.pbix` now contains a Complaint Overview page with:

- a weekly narrative-complaint trend for the complete monitoring weeks;
- four KPI cards: Narrative Complaints, Monitored Complaints, Persistent Alerts, and Alerted Topics;
- a horizontal bar chart of persistent alerts by severity;
- a visible note explaining the time window, the difference between imported and monitored complaint counts, and the non-prevalence limitation.

The separate Emerging Risk Alerts page still contains its earlier evidence table. The report is a local Power BI Desktop artifact, not a published dashboard.

## Measures and meaning

```DAX
Narrative Complaints = DISTINCTCOUNT(complaints[complaint_id])
Monitored Complaints = SUM(weekly_overview[narrative_complaints])
Persistent Alerts = COUNTROWS(alerts)
Alerted Topics = DISTINCTCOUNT(alerts[topic_id])
```

| Measure | Verified unfiltered result | Meaning |
|---|---:|---|
| Narrative Complaints | 318,804 | Unique imported narrative complaint IDs |
| Monitored Complaints | 315,623 | Complaints in 30 complete monitoring weeks |
| Persistent Alerts | 11 | Alert records passing the persistence rule |
| Alerted Topics | 7 | Distinct topics represented among those alerts |

The cards currently abbreviate the two large values as `319K` and `316K`. The exact values are written in the page note and were reconciled with the exports. Do not read the two rounded labels as equal: the imported complaint table includes a partial week that is excluded from monitoring. The complete-week trend runs from 4 September 2023 through 25 March 2024.

The severity chart shows 3 `high` and 8 `review` alerts, totaling 11. Severity is a statistical investigation priority, **not** a measure of consumer harm.

## Model and interaction decisions

`topics[topic_id]` actively filters `complaints`, `weekly_topics`, `alerts`, and `product_topics` through one-to-many, single-direction relationships. Two Power BI auto-detected relationships from product fields to `model_class_performance` were made inactive because the evaluation table is not a product dimension.

Selecting `high` in the severity chart reduces Persistent Alerts and Alerted Topics to 3 each. The overall complaint and complete-week totals remain unchanged. The selection was cleared after verification.

No date, product, or topic slicer was added to this page. The current model lacks shared date and product dimensions across all overview facts, and adding one now would make some KPI cards respond while others stayed fixed. A future dashboard milestone can add shared dimensions and then test consistent slicer behavior.

## Validation and responsible interpretation

- The eight imported table row counts were checked in Power BI Desktop: complaints 318,804; topics 30; weekly topics 900; alerts 11; product topics 244; weekly overview 30; model summary 1; model class performance 11.
- `complaints[date_received]`, `complaints[week_start]`, and `weekly_topics[week_start]` were confirmed as Date; checked topic keys were Whole Number.
- The weekly-overview export sums to 315,623 complaints and 11 alerts; the alerts export contains 7 unique topics and a 3/8 high/review split.
- The overview visual layout and severity interaction were inspected in Power BI Desktop, and the PBIX was saved.
- CFPB complaint counts must not be presented as population prevalence, company-quality rankings, or proof that an alert caused harm.

## Interview defense

**Why are there two complaint counts?** The full import contains 318,804 unique narrative complaints, but the detector evaluates 30 complete weeks containing 315,623 complaints. The incomplete week is excluded so its low volume does not distort historical monitoring.

**Why are there no slicers yet?** A slicer is useful only when its filter path and scope are clear. Here, a date or product slicer would not consistently filter every card. Shared dimensions and interaction testing should precede exposing those controls.

**Does an alert mean a financial institution did something wrong?** No. It indicates that a complaint theme met a historical-change and persistence rule and merits human review. The CFPB database is not representative of all consumers.

## Remaining dashboard work

Finish the topic-monitoring, alert-investigation, product/geography, and model-quality views; add any shared dimensions needed for consistent filters; perform broader visual and reconciliation QA. Publishing or public sharing remains a separate user-approved decision. Main README updates are deferred until the project-final documentation pass.
