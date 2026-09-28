# Data contract

## Source

The narrative source is the official CFPB Consumer Complaint Database Narratives Archive in the CFPB FOIA Reading Room.

Selected archive:

```text
CCDB Export 5 — September 2023 through March 2024
```

Acquisition settings are versioned in `configs/dataset.yaml`. The archive is downloaded and verified with:

```powershell
$env:PYTHONPATH = "src"
python -m complaint_intelligence.acquisition
```

The command refuses silent overwrites. It streams into a temporary `.part` file, validates the expected byte count, tests ZIP integrity, rejects unsafe archive paths, calculates SHA-256, and writes `data/raw/snapshot_metadata.json`.

After acquisition, safely extract and inspect the configured member with:

```powershell
$env:PYTHONPATH = "src"
python -m complaint_intelligence.inspection
```

This command re-verifies the archive against its metadata, extracts through a temporary file, checks the exact uncompressed byte count, calculates the extracted CSV hash, validates encoding and delimiter, confirms required columns, and scans the CSV in chunks. It writes local metadata under `data/raw/` and the schema report under `data/interim/`; all generated data remains ignored by Git.

## Data layers

```text
data/raw/        immutable official archive and extracted source
data/interim/    validated or filtered intermediate records
data/processed/  reproducibly generated modelling tables
```

All three data directories are excluded from Git except for their placeholder files.

## Required conceptual fields

The extraction and schema-audit milestone must verify:

- `Complaint ID` — stable record identifier;
- `Date received` — time axis for splitting and monitoring;
- `Product` — candidate classification target;
- `Issue` and `Sub-issue` — finer-grained labels and analysis dimensions;
- `Consumer complaint narrative` — primary NLP input;
- `Company`, `State`, and `Submitted via` — optional analysis dimensions;
- company-response fields — retrospective context, not arrival-time model inputs.

Exact archived column names must be inspected before transformation code depends on them.

For the selected archive, the inspection has verified all five required fields. See `notes/04b_schema_inspection.md` for the measured schema and quality results.

## Rules

1. Preserve the raw archive without manual edits.
2. Record source URL, download time, byte size, hash, and ZIP members.
3. Inspect and validate the schema before extracting modelling fields.
4. Never commit raw complaint text or generated datasets.
5. Use only information available at the defined prediction time.
6. Treat narrative availability as a historical selection mechanism.
7. Document label consolidation rather than silently dropping rare classes.
8. Do not interpret complaint volume as population prevalence or a company-quality ranking.

