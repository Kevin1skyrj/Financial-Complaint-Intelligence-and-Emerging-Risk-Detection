# Weekly Emerging-Risk Detection

## Milestone outcome

This milestone converts complaint-topic assignments into weekly monitoring signals. It detects
topics whose share of weekly narrative volume rises unusually relative to their own recent
history, then requires persistence before creating an analyst-review alert.

Implemented command:

```powershell
$env:PYTHONPATH = "src"
python -m complaint_intelligence.risk_detection
```

The system is a retrospective monitoring experiment on an archived dataset. An alert means
"investigate this change," not "harm or misconduct has been proven."

## Why monitor topic share instead of only count?

Total complaint volume changes substantially over time. A topic's count can rise merely because
all complaints increased. Topic share divides the topic count by total narrative complaints that
week:

```text
topic share = topic complaints in week / all narrative complaints in week
```

Share is not perfect—it can rise when other topics fall—but it provides a more comparable signal
than raw volume alone. Both count and share remain in the output for investigation.

## Time coverage

The archive starts on Friday, September 1, 2023. The partial opening week is excluded so it cannot
distort the first baseline. Monitoring covers 30 complete Monday-to-Sunday weeks:

```text
2023-09-04 through 2024-03-31
```

All 30 topics receive a row for every week, including zero-count combinations. The final weekly
table therefore contains 900 topic-week rows.

## Prior-only rolling baseline

Every topic is compared only with its own earlier observations:

- rolling lookback: 8 prior weeks;
- minimum history: 6 prior weeks;
- baseline center: median topic share;
- baseline scale: median absolute deviation multiplied by 1.4826;
- minimum scale floor: 0.0001.

The current week is never included in its baseline. This prevents the spike being evaluated from
diluting its own anomaly score and avoids future leakage.

## Robust anomaly score

For a topic and week:

```text
robust z = (current share - prior median share) / robust prior scale
```

Median and median absolute deviation are less sensitive to earlier spikes than mean and standard
deviation. The scale floor prevents nearly constant historical series from creating division by
zero or infinitely large scores.

A candidate signal requires all of the following:

- robust z-score at least 3.5;
- at least 100 complaints in the current week;
- topic-share increase of at least 0.001, or 0.1 percentage points;
- at least 6 historical weeks available.

These thresholds were configured before reviewing the resulting alerts.

## Persistence rule

A single candidate spike does not create an alert. The current week must be a candidate and at
least two of the latest three weeks must be candidates.

This rule reduces one-week noise while allowing a brief interruption. It is a pragmatic monitoring
policy rather than a statistically optimal threshold.

Alert severity is:

- `high` when a persistent alert has robust z-score at least 7;
- `review` for other persistent alerts;
- `none` otherwise.

Severity prioritizes analyst attention; it does not measure actual consumer harm.

## Verified backtest results

| Result | Count |
|---|---:|
| Complete weeks | 30 |
| Topics monitored | 30 |
| Topic-week rows | 900 |
| Candidate signals | 30 |
| Persistent alerts | 11 |
| Distinct alerted topics | 7 |

The persistence filter reduced 30 candidate spikes to 11 reviewable alerts.

## Highest-scoring persistent alerts

| Topic | Week | Count | Topic share | Prior median share | Robust z | Terms |
|---:|---|---:|---:|---:|---:|---|
| 28 | 2023-12-18 | 499 | 5.02% | 1.86% | 9.89 | consumer, information, reporting, USC |
| 12 | 2024-02-26 | 498 | 4.00% | 1.80% | 8.44 | matter, rectify, financial, resolution |
| 18 | 2023-11-06 | 389 | 3.99% | 2.61% | 7.51 | inquiries, unauthorized, credit |
| 7 | 2023-11-27 | 602 | 6.60% | 5.18% | 6.31 | money, called, account |
| 28 | 2023-12-25 | 419 | 4.79% | 1.95% | 6.27 | consumer, information, reporting, USC |
| 12 | 2024-03-04 | 587 | 4.32% | 1.92% | 5.80 | matter, rectify, financial, resolution |
| 5 | 2023-11-13 | 112 | 1.21% | 0.36% | 5.71 | authorize, credit report, inquiry |
| 0 | 2023-10-23 | 560 | 6.17% | 4.96% | 5.63 | payment, paid, late, account |

Other persistent alerts include another unauthorized-inquiry week, a March credit-report theme,
and a second week for topic 5.

## How to interpret the alerts

Some alerts represent understandable consumer themes, such as unauthorized inquiries or payment
problems. Others are dominated by legal, templated, or broad language. Possible explanations
include:

- a genuine increase in a consumer problem;
- repeated complaint templates or coordinated submission language;
- changes in reporting or narrative-publication behavior;
- seasonal effects;
- cluster-assignment drift;
- a small historical scale producing a large standardized score.

The detector cannot distinguish these causes automatically. An analyst should inspect volume,
topic terms, product/company composition, and privacy-controlled representative complaints before
escalation.

## Generated artifacts

- `data/processed/risk/weekly_topic_metrics.csv` — every topic-week count, share, baseline,
  anomaly score, candidate flag, persistence count, and alert flag;
- `data/processed/risk/emerging_risk_alerts.csv` — the 11 persistent alerts;
- `data/processed/risk/risk_detection_report.json` — configuration, hashes, coverage, artifacts,
  and the ten highest-scoring alerts.

These files contain topic terms and aggregate metrics but no complaint narratives.

## Testing without labelled incidents

The CFPB archive does not provide ground-truth labels saying which week contained a newly emerging
risk. Therefore precision and recall for alerts cannot honestly be calculated.

The automated tests instead verify behavior with controlled synthetic data:

- a persistent two-week spike creates an alert;
- a one-week spike does not pass persistence;
- the baseline contains only prior weeks;
- missing topic-week combinations are filled with zero;
- weekly topic shares sum to one;
- invalid persistence settings fail clearly.

This validates implementation logic, not real-world alert usefulness.

## Limitations

- Only 30 complete weeks are available.
- There are no labelled real-world incidents for alert evaluation.
- Topic quality is limited by the low-silhouette TF-IDF clustering model.
- Fixed thresholds were not calibrated against operational review capacity.
- Topic-share monitoring can miss broad increases affecting every topic.
- Duplicate and templated complaints can create a legitimate volume signal or a misleading spike.
- The scale floor influences scores for historically stable topics.
- Multiple topic tests increase the chance of false alarms.
- No seasonality model is defensible with only seven months of data.

## Responsible-use boundary

Alerts are investigation signals only. They must not be used as proof of fraud, misconduct,
system failure, or institution quality. The system makes no lending, eligibility, pricing,
enforcement, or adverse-action decisions.

## Verification

- Complete automated suite: 45 tests passed.
- All 318,804 topic assignments were used as the source.
- The incomplete opening week was excluded.
- The real detector produced 30 candidates and 11 persistent alerts.
- Weekly and alert artifact hashes were recorded.
- Outputs contain no narrative text.
- A date-serialization failure found during the first run was corrected and the pipeline reran
  successfully with controlled overwrite.

## Interview defense

**Why use a rolling baseline?**

Complaint language and volume can drift. A rolling baseline compares each topic with its recent
behavior rather than assuming the entire seven-month period is stationary.

**How did you prevent leakage?**

Every weekly score uses only the previous eight weeks. The current and future weeks are excluded
from the baseline window.

**Why require persistence?**

One unusual week can result from processing noise or templates. Requiring two candidate weeks
within three weeks reduces isolated false alarms and prioritizes sustained changes.

**How do you know the 11 alerts are real risks?**

I do not. They are statistically unusual topic-share changes in an archived complaint sample.
Without labelled incidents and analyst review, I can validate detector behavior but cannot claim
real-world alert precision.

**Why not use Isolation Forest or a neural anomaly detector?**

The available history is short, and a transparent rolling score is easier to audit and explain.
More complex models would still lack ground-truth incidents. Complexity should follow better data
and evaluation, not replace them.

## Next milestone

The next milestone will turn the classification, topic, and alert artifacts into analytical SQL
tables and queries suitable for a Power BI dashboard.

