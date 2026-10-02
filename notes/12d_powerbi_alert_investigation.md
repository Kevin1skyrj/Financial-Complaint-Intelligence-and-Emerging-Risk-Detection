# Power BI Alert Investigation: From Signal to Complaint Metadata

## Milestone outcome

The local `powerbi/Financial_Complaint_Intelligence.pbix` now has an interactive **Emerging Risk Alerts** investigation page. Its existing 11-row alert table was expanded with observed topic share, prior median share, share increase, and persistence count. A second table displays complaint **metadata** for the selected alert's exact topic and week. No complaint narrative text is imported or displayed.

This is a local Power BI Desktop report, not a published dashboard. The main README remains deferred until the final project documentation pass.

## How to use the page

1. Open **Emerging Risk Alerts**.
2. Select one row in the upper alert table. The lower table then shows complaint ID, company, date received, issue, product, and state for that alert's topic and Monday-to-Sunday week.
3. Select another alert row to compare its underlying complaint metadata. With no alert selected, the lower table is intentionally empty.
4. Scroll the upper table horizontally if the full cluster `top_terms` text is needed. Severity, topic ID, count, robust z-score, week, share, baseline, increase, and persistence are placed before those long terms.

The upper table disables its total row. Summing z-scores, shares, share increases, or persistence counts over different alerts would be misleading. The lower table also disables totals. Observed share, historical median, and share increase display four decimal places, while the CSV exports retain full precision. These numbers are **fractions**: `0.0137` is about a **1.37 percentage-point** increase, not a 0.0137% increase.

## Cross-table filtering implementation

The model's `topics` dimension filters both `alerts` and `complaints`, but an `alerts` row does not naturally filter `complaints` through that single-direction relationship. A measure in the complaints table explicitly checks both keys:

```DAX
Selected Alert Complaint =
VAR SelectedTopic = SELECTEDVALUE(alerts[topic_id])
VAR SelectedWeek = SELECTEDVALUE(alerts[week_start])
RETURN
    IF(
        NOT ISBLANK(SelectedTopic)
            && NOT ISBLANK(SelectedWeek)
            && SELECTEDVALUE(complaints[topic_id]) = SelectedTopic
            && SELECTEDVALUE(complaints[week_start]) = SelectedWeek,
        1,
        0
    )
```

The lower table has a visual-level filter requiring `Selected Alert Complaint = 1`; the helper measure is not shown as a table column. Complaint ID is set to **Don't summarize**, since adding IDs together is meaningless. `date_received` uses the raw date rather than Power BI's Year/Quarter/Month/Day hierarchy.

The filter requires a single selected topic and week. It is a contextual inspection control, not a direct fact-to-fact relationship or a general-purpose cross-filter for every visual. If multi-select is introduced, this measure must be redesigned and tested.

## Reconciliation and visual QA

- The `alerts.csv` export has 11 records: 3 `high` and 8 `review`.
- Topic 18's `high` alert on 6 November 2023 records 389 topic complaints, observed share `0.0398647`, prior median `0.0261483`, increase `0.0137164`, robust z-score `7.5141`, and persistence count `2`.
- Filtering the independently exported `complaints.csv` by `topic_id = 18` and `week_start = 2023-11-06` returns **389 rows**, matching the alert count.
- Selecting a topic 5 alert in the Power BI table changed the lower table to its November week; selecting topic 18's 6 November alert changed the lower table to complaint dates in that week. This verifies that both topic and week are used rather than topic alone.
- The page layout, field types, hidden helper column, total-row settings, and four-decimal share display were inspected in Power BI Desktop. The PBIX was saved after these checks.

## What the page does not prove

An alert identifies a statistically unusual, persistent change worthy of human review. It does not establish causation, consumer harm, misconduct, or a reliable ranking of companies. CFPB complaint submissions are not a representative sample of all consumers. The table's company names are context for investigation, not a company performance league table. The source narratives are deliberately absent from the report; the issue field is the public structured category, not the consumer's free-text account.

## Publication boundary and later completion

The PBIX imports complaint IDs and other metadata even though it does not contain narratives. The
later final review accepted that structured public metadata for this portfolio scope while keeping
raw narratives and generated CSV exports excluded. Product/geography, model-quality, and
report-wide QA were subsequently completed; see
[`12e_powerbi_completion_and_validation.md`](12e_powerbi_completion_and_validation.md). No report
was published to the Power BI service.
