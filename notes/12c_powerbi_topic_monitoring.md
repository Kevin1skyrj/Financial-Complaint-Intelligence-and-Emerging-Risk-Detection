# Power BI Topic Monitoring: Weekly Signal Investigation

## What was built

The local `powerbi/Financial_Complaint_Intelligence.pbix` now has a third page, **Topic Monitoring**. A single-select `topics[topic_id]` dropdown filters a topic descriptor, a 30-week line chart, and a weekly evidence table. It opens on topic 18, an unauthorized-credit-inquiry theme. Selecting another topic changes all three visuals; this was checked with topic 19 and then reset to 18.

The descriptor shows `topics[top_terms]` and `topics[dominant_product]`. These are clustering summaries, not a human-validated diagnosis of every complaint in the topic.

## Visuals and data lineage

| Visual | Fields | Question answered |
|---|---|---|
| Topic selector | `topics[topic_id]` | Which theme is under review? |
| Topic descriptor | `topics[top_terms]`, `topics[dominant_product]` | What language and product dominate this cluster? |
| Weekly line chart | `weekly_topics[week_start]`, `weekly_topics[topic_share]`, `weekly_topics[baseline_share_median]` | Did this topic's share rise above its prior-history median? |
| Weekly evidence table | `week_start`, `topic_count`, `robust_z_score`, `persistent_signal_count`, `severity`, `topic_share` from `weekly_topics` | What counts and detection evidence accompany each week? |

Both plotted share values are **fractions** of narrative complaints, not percentages on the current chart axis: `0.04` means about 4%. The baseline is a rolling median of prior observations. It is a comparison line, **not** the alert cutoff by itself. The line-chart fields use Power BI's Sum aggregation; with one row per topic-week and a single selected topic, that equals the underlying weekly value. Changing this page to allow multiple topics would require revisiting aggregation and labeling.

The table's total row is disabled. Summing weekly z-scores, persistence counts, or shares would produce numbers with no useful investigation meaning. The table is scrollable so all 30 weeks remain available.

## Detection logic behind the page

The upstream detector compares each topic with its own previous eight weeks, requiring at least six prior weeks. It scores the rise using a median/MAD-based robust z-score. A candidate additionally needs z-score at least 3.5, at least 100 topic complaints, and a share increase of at least 0.001 (0.1 percentage points). A persistent alert needs the current candidate plus at least two candidate weeks among the latest three. See `notes/11_emerging_risk_detection.md` for the full algorithm and its limits.

The `severity` column is an investigation priority. `none` does not mean the theme is harmless; `high` does not prove harm or misconduct.

## Validation example: topic 18

The filtered topic descriptor reads as unauthorized credit inquiries and a credit-reporting dominant product. The generated `weekly_topics.csv` records for the week starting 6 November 2023: 389 topic complaints out of 9,758 monitored complaints, topic share `0.0398647`, prior median share `0.0261483`, robust z-score `7.5141`, persistence count `2`, and severity `high`. The following week has a `review` alert. The line chart visibly rises near the first alert week. Switching the dropdown to topic 19 changed the descriptor, chart trajectory, and evidence rows, confirming the topic filter path.

Power BI Desktop saved the PBIX after the interaction test. This is a local report, not a published or publicly shared dashboard. No main README update, staging, commit, or push was performed.

## Interview defense and limitations

**Why share rather than raw count alone?** Overall complaint volume changes. Topic share normalizes a topic count by that week's narrative complaint total, while the table retains raw count for context.

**Why does the baseline start later?** The prior-only calculation needs at least six complete historical weeks. Early weeks lack enough history and should not be interpreted as zero-risk weeks.

**Does a line crossing the median create an alert?** No. The score, minimum count, minimum share increase, and persistence rules must all be considered. The median is descriptive context, not the full decision rule.

**Can we compare products or institutions using this page?** No. CFPB submissions are not a representative sample of all consumers. Topic terms are machine-generated; the page supports analyst triage of changes within this dataset, not prevalence estimates, institution rankings, or causal claims.

## Later completion

The alert-investigation, product/geography, and model-quality pages were subsequently completed.
The report-wide QA, privacy review, and final completion boundary are recorded in
[`12e_powerbi_completion_and_validation.md`](12e_powerbi_completion_and_validation.md).
