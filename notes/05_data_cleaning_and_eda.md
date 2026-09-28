# Data Cleaning and Exploratory Data Analysis

## Milestone outcome

This milestone converts the immutable extracted CFPB archive into a reproducible,
narrative-only intermediate dataset and produces a privacy-safe aggregate EDA report.
It does **not** preprocess language, choose a final prediction target, split data, or train
a model.

Implemented command:

```powershell
$env:PYTHONPATH = "src"
python -m complaint_intelligence.preparation
```

The command reads the source in 50,000-row chunks, refuses silent overwrites, writes through
a temporary `.part` file, and records the prepared file's size and SHA-256. Generated files
remain under `data/interim/` and are ignored by Git.

## Why create an intermediate dataset?

The raw archive is evidence and must remain unchanged. The intermediate layer gives later
experiments a stable input containing only records that can support narrative NLP. It also
keeps transformation logic repeatable instead of relying on manual notebook edits.

The output columns are:

| Column | Purpose |
|---|---|
| `complaint_id` | Record identity and traceability |
| `date_received` | Temporal splitting and weekly monitoring |
| `product`, `sub_product` | Candidate labels and analysis dimensions |
| `issue`, `sub_issue` | Finer complaint taxonomy |
| `narrative` | NLP input text |
| `company`, `state`, `submitted_via` | Optional descriptive analysis, not default model features |

Fields describing the company's later response are deliberately excluded because they would
not be known when a new complaint first arrives. Using them would create prediction-time
leakage.

## Cleaning decisions

### What was changed

- Rows with a missing, empty, or whitespace-only narrative were excluded.
- Leading and trailing narrative whitespace was removed.
- Column names were converted to consistent `snake_case` names.
- Valid received dates were serialized as ISO `YYYY-MM-DD` values.
- Only the explicitly configured columns were retained.

### What was deliberately not changed

- Narratives were not lowercased, stemmed, lemmatized, or stripped of punctuation.
- Stop words were not removed.
- Exact duplicate narratives were measured but not removed.
- Rare products or issues were not merged or discarded.
- Company and geography fields were not imputed.

These choices preserve information until the modelling goal and validation design are fixed.
In particular, deduplication must be coordinated with the temporal split: duplicate text on
both sides of a split can inflate evaluation results, but deleting every repeated narrative
may also remove real repeated events or complaint templates that matter operationally.

## Verified filtering funnel

| Stage | Rows | Share of source |
|---|---:|---:|
| Extracted archive | 945,532 | 100.00% |
| Missing/blank narrative | 626,728 | 66.28% |
| Narrative rows written | 318,804 | 33.72% |

This means the NLP dataset is a selected subset, not a representative sample of every CFPB
complaint. Consumers choose whether to permit narrative publication, and publication rules
also affect availability.

## Narrative length

| Statistic | Characters | Words |
|---|---:|---:|
| Minimum | 10 | 1 |
| 25th percentile | 311 | 55 |
| Median | 647 | 115 |
| 75th percentile | 1,149 | 202 |
| 95th percentile | 3,053 | 528 |
| 99th percentile | 6,467 | 1,132 |
| Maximum | 32,962 | 5,911 |

The long right tail matters. A linear TF-IDF baseline can accept variable-length documents,
while later transformer experiments would require an explicit truncation or chunking policy.
The maximum should not dictate a universal sequence length.

## Exact duplicate audit

After trimming only outer whitespace:

- 214,661 unique narrative hashes were found across 318,804 narrative rows;
- 23,447 hashes occurred more than once;
- 127,590 rows belonged to a repeated-text group;
- 104,143 rows were redundant occurrences beyond the first copy.

Only SHA-256 hashes and aggregate counts enter the report; raw complaint text does not.
The repeated-text rate is large enough that a random row split would have a serious leakage
risk. Before modelling, duplicates must be grouped so identical narratives cannot cross train,
validation, and test boundaries. Whether repeated rows remain in the training set is a separate
experiment and must be documented.

## Label and narrative-availability findings

The archive is highly concentrated in **Credit reporting or other personal consumer reports**:
781,459 total complaints. Only 226,564 of those have narratives, a 28.99% narrative rate.
Other large product groups have much higher narrative availability:

| Product | Total | With narrative | Availability |
|---|---:|---:|---:|
| Credit reporting or other personal consumer reports | 781,459 | 226,564 | 28.99% |
| Debt collection | 50,752 | 26,896 | 52.99% |
| Credit card | 36,975 | 21,409 | 57.90% |
| Checking or savings account | 27,319 | 15,319 | 56.07% |
| Mortgage | 12,597 | 7,157 | 56.82% |
| Student loan | 10,629 | 6,162 | 57.97% |

This unequal availability changes the label distribution in the narrative-only dataset. A
model trained on published narratives learns from that selected distribution; it must not be
presented as a classifier for all consumer complaints without qualification.

There are 88 issue labels, including very small classes. Issue-level classification would
therefore require a documented consolidation or minimum-support strategy. Product is the more
defensible first supervised target, but the exact baseline scope will be fixed in the next
modelling-design milestone rather than silently decided here.

## Temporal findings

All source dates parsed successfully. Narrative volume by month was:

| Month | Narrative complaints |
|---|---:|
| 2023-09 | 42,517 |
| 2023-10 | 43,349 |
| 2023-11 | 38,894 |
| 2023-12 | 40,851 |
| 2024-01 | 43,920 |
| 2024-02 | 48,111 |
| 2024-03 | 61,162 |

The increasing volume could reflect reporting, processing, publication, or real complaint
changes. It is not automatically evidence that consumer harm increased. Later experiments must
split chronologically and interpret alert signals relative to the observed data-generating
process.

## Privacy and responsible use

- Versioned reports contain aggregates, lengths, and hashes—not narrative examples.
- Raw and intermediate complaint text remains Git-ignored.
- `company` must not become a shortcut feature for product prediction unless explicitly tested
  and justified.
- Complaint counts cannot rank company quality because exposure, customer base, submission
  behavior, and publication selection are not controlled.
- Topic or risk alerts are triage signals for human review, not proof of wrongdoing.

## Verification

- Full archive scanned in chunks: 945,532 rows.
- Prepared narrative dataset written: 318,804 rows.
- Automated suite: 20 tests passed.
- The tests cover filtering, trimming, date normalization, duplicate aggregation, privacy-safe
  reports, missing-column failure, and overwrite protection.
- Ruff was unavailable in the local environment; compilation and Git diff validation were used
  in addition to the test suite.

## Interview defense

**Why did you not clean the text aggressively?**

I separated record-level cleaning from model-specific text preprocessing. At this stage I only
removed unusable rows and normalized storage. Lowercasing, tokenization, and stop-word decisions
depend on the chosen representation and should be tested inside the training pipeline to prevent
train/test inconsistency.

**Why are duplicates important?**

Over 104,000 rows are repeated occurrences beyond the first identical narrative. If identical
text appears in both training and test data, the score may measure memorization rather than
generalization. I measured duplicates now and will group them when constructing the temporal
evaluation split.

**Why not interpret the rise in March as an emerging risk?**

Volume alone mixes real behavior with database coverage, consent, seasonality, and processing
effects. Emerging-risk detection needs topic-level baselines, persistence rules, and human
review; this EDA only establishes the time series and its limitations.

## Next decision

The next milestone will define leakage-safe text preprocessing and a chronological,
duplicate-aware experiment design. No performance claim should be made before that split is
implemented and frozen.
