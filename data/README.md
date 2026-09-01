# Data contract

Planned source: the official CFPB Consumer Complaint Database.

Place a downloaded CSV at `data/raw/complaints.csv`. Raw, interim, and processed data are ignored by Git.

## Initial fields

The first milestone will validate and document at least:

- `Complaint ID` — stable record identifier;
- `Date received` — time axis for monitoring;
- `Product` — initial classification target;
- `Issue` and `Sub-issue` — finer-grained labels and analysis dimensions;
- `Consumer complaint narrative` — model input when publicly available;
- `Company`, `State`, and `Submitted via` — analysis dimensions;
- `Company response to consumer` and `Timely response?` — outcome context, not automatically valid prediction features.

Field names must be checked against the downloaded snapshot before code depends on them.

## Rules

1. Record source URL, download date, file hash, row count, and schema.
2. Never commit raw complaint text or generated datasets.
3. Use only information available at the defined prediction time.
4. Treat missing narratives as a data-selection issue, not empty text.
5. Document label consolidation rather than silently dropping rare classes.
6. Do not infer that complaint volume represents population-level prevalence.

