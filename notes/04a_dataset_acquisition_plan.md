# 04A — Dataset Acquisition Plan

## 1. Purpose of this note

This note defines exactly which data file we intend to acquire, why we selected it, where it will be stored, what metadata must be recorded, and how we will verify it before analysis.

This document began as an acquisition plan. The download and archive-verification portion was implemented on September 28, 2026. Extraction, schema inspection, row counting, and analysis remain separate later steps.

Current status:

- the official archive has been downloaded into the Git-ignored raw-data directory;
- its byte count, SHA-256, ZIP integrity, and member paths have been verified;
- its contents have not been extracted;
- no schema, row count, class distribution, or model result is claimed yet.

This controlled sequence prevents a “download a CSV and start modelling” workflow.

## 2. Authoritative source

The narrative data will come from the official CFPB FOIA Reading Room:

- [CFPB Consumer Complaint Database Narratives Archive](https://www.consumerfinance.gov/foia-requests/foia-electronic-reading-room/cfpb-consumer-complaint-database-narratives-archive/)

The archive contains complaint records that were previously published in the Consumer Complaint Database. It covers complaints received from December 1, 2011 through August 14, 2026.

We are using the archive because the CFPB stopped publishing complaint narratives in the live database in August 2026 and removed narratives from the live database in its September 2026 release.

## 3. Candidate archives inspected

We inspected the HTTP metadata of four official archive files without downloading their contents.

| Archive period | Compressed bytes | Approximate MiB | Time coverage |
|---|---:|---:|---:|
| September 2023–March 2024 | 100,880,669 | 96.21 MiB | 7 months |
| April 2024–July 2024 | 77,142,558 | 73.57 MiB | 4 months |
| August 2024–October 2024 | 71,365,591 | 68.06 MiB | 3 months |
| November 2024–December 2024 | 52,563,546 | 50.13 MiB | 2 months |

The server reported `application/zip` for each file and a last-modified timestamp of September 14, 2026.

These byte sizes describe the compressed downloads. The extracted data can be considerably larger, so free disk space must be checked before downloading.

## 4. Selected candidate archive

### Archive

**CCDB Export 5 — September 2023 through March 2024**

### Official URL

```text
https://files.consumerfinance.gov/f/documents/CCDB_Export_5_September_2023_through_March_2024.zip
```

### Expected compressed size

```text
100,880,669 bytes
```

### Why this archive was selected

#### Sufficient temporal coverage

Seven months provides roughly thirty weekly periods. That is much more useful for a retrospective emerging-theme experiment than a two-, three-, or four-month archive.

It should allow us to create, subject to actual data quality:

- an earlier training period;
- a validation period;
- a later test period;
- rolling historical theme baselines;
- several weeks for retrospective alert evaluation.

#### Manageable download size

Approximately 96 MiB compressed is substantial enough to contain useful data but still manageable on a local development machine.

#### More consistent taxonomy period

The CFPB lists a product and issue form update beginning in August 2023. The selected archive begins in September 2023, so it is contained within the post-August-2023 taxonomy period.

This does not prove every label remains perfectly stable, but it reduces the known cross-taxonomy complication that would arise from mixing pre- and post-update records.

#### Reproducible historical boundary

The archive is a fixed historical file rather than a live query whose results may change daily.

## 5. Why the smallest archive was not selected

The November–December 2024 archive is only about 50 MiB compressed, but two months is weak for the emerging-risk objective.

With such a short period:

- there would be few weekly observations;
- historical baselines would be unstable;
- train, validation, and test periods would be compressed;
- an apparent spike could be dominated by short-term noise;
- seasonality and persistent patterns could not be studied meaningfully.

The project is not only a classifier, so archive selection must consider temporal monitoring as well as model training.

## 6. Why we are not downloading every archive

Downloading every historical file immediately would increase:

- storage requirements;
- processing time;
- taxonomy inconsistency;
- duplicate and overlap checks;
- debugging complexity;
- the risk of performing analysis before understanding the source.

We will prove the full pipeline on one fixed archive first. Additional periods can be introduced later for external temporal validation if the initial system is reliable.

## 7. Planned local paths

The archive and extracted raw records will remain outside Git.

```text
data/
├── raw/
│   ├── CCDB_Export_5_September_2023_through_March_2024.zip
│   ├── extracted archive file or files
│   └── snapshot_metadata.json
├── interim/
│   └── validated and filtered intermediate records
└── processed/
    └── modelling-ready records
```

### Raw-data rule

Files under `data/raw/` must be treated as immutable inputs. We will not manually edit the extracted CSV or spreadsheet.

If a source problem is found, the transformation code must handle it reproducibly and write a new interim artifact.

## 8. Pre-download checks

Before downloading, we must verify:

1. The URL still belongs to `files.consumerfinance.gov`.
2. The response status is successful.
3. The content type indicates a ZIP archive.
4. The reported compressed size is still expected or any change is documented.
5. The destination is exactly the project's `data/raw/` directory.
6. Sufficient free disk space exists for both the ZIP and extracted contents.
7. The destination filename does not already contain an unverified older download.

We will not overwrite an existing archive silently.

## 9. Download metadata contract

After a successful download, create `data/raw/snapshot_metadata.json` containing at least:

```json
{
  "source_authority": "Consumer Financial Protection Bureau",
  "source_page": "official narrative archive page",
  "archive_url": "exact official ZIP URL",
  "archive_period": "September 2023 through March 2024",
  "downloaded_at_utc": "actual timestamp",
  "archive_filename": "actual local filename",
  "compressed_bytes": "actual size",
  "sha256": "calculated file hash",
  "archive_members": ["actual filenames inside ZIP"],
  "notes": "any observed source or download conditions"
}
```

The example above is a contract, not completed metadata. Placeholder text must be replaced with actual observed values.

## 10. Why calculate SHA-256?

SHA-256 produces a content fingerprint for the downloaded archive.

It helps answer:

- Are two files identical even if their filenames match?
- Did the file change between runs?
- Can another person verify they used the same archive?
- Was the local file corrupted or replaced?

A matching hash does not prove that the data is correct or unbiased. It only helps establish file identity and integrity.

## 11. Archive inspection before extraction

Before extracting, we will list the ZIP members and record:

- number of contained files;
- member filenames;
- reported uncompressed sizes;
- file extensions;
- unexpected nested paths;
- duplicate filenames;
- suspicious absolute or parent-directory paths.

This is both a reproducibility and safety step. Extraction code should reject archive members that attempt to escape the intended destination directory.

## 12. Schema verification after extraction

We will read only the header and a small sample first.

We must verify:

- actual delimiter;
- text encoding;
- exact column names;
- quoted multiline narrative handling;
- date format;
- complaint ID representation;
- presence of the narrative column;
- whether multiple files use the same schema;
- whether archived names differ from the current live field reference.

No processing code should depend on assumed column names until this check is complete.

## 13. Minimum expected fields

The project needs the following conceptual fields:

| Concept | Expected source field | Required for |
|---|---|---|
| Record identifier | `Complaint ID` | Traceability and duplicate checks |
| Received date | `Date received` | Temporal splitting and monitoring |
| Narrative | `Consumer complaint narrative` or archive equivalent | NLP input |
| Product | `Product` | Candidate target and analysis |
| Issue | `Issue` | Candidate target and analysis |
| Sub-product | `Sub-product` | Taxonomy analysis |
| Sub-issue | `Sub-issue` | Taxonomy analysis |

If identifier, received date, narrative, product, or issue is absent, we must stop and reassess the archive rather than silently continue.

## 14. Initial loading strategy

The archive may extract to a file much larger than the compressed ZIP. We will not assume it can be loaded into memory in one operation.

The first loader should support chunked inspection:

```text
Open extracted file
        ↓
Read one manageable chunk
        ↓
Validate required columns
        ↓
Collect counts and data-quality summaries
        ↓
Continue with the next chunk
```

Chunking helps control memory usage, but it introduces design considerations:

- duplicate IDs can occur across chunks;
- global class counts require aggregation;
- exact narrative duplicate detection needs a cross-chunk strategy;
- data types must remain consistent;
- summaries must reconcile with the final row count.

We will choose an actual chunk size only after inspecting the extracted file size and available memory.

## 15. Initial row-filtering policy

The raw archive will be preserved in full. A processed NLP dataset may later require:

- valid complaint ID;
- parseable received date;
- non-empty narrative;
- non-empty candidate target label;
- removal or controlled handling of exact duplicate records;
- documented handling of rare labels.

These are planned rules, not yet applied decisions. We must first measure how many rows each rule would remove.

The audit must show a filtering funnel:

```text
Source rows
  - malformed records
  - duplicate complaint IDs
  - invalid dates
  - unavailable or empty narratives
  - unavailable target labels
  - any justified target-scope exclusions
= final modelling rows
```

## 16. Overlap and taxonomy checks

The selected archive starts after the August 2023 form update, but we will still verify:

- earliest and latest received dates in the file;
- whether all rows fall within the advertised period;
- whether unexpected older or newer records exist;
- product and issue values over time;
- labels appearing only in a small portion of the period;
- product–issue combinations with inconsistent mappings.

Archive title and actual record dates must not be assumed to match perfectly without measurement.

## 17. Temporal split planning

The seven-month archive gives us room to consider a chronological split.

An illustrative—not final—structure could be:

```text
Earlier months  -> training
Next period     -> validation
Latest period   -> test
```

The exact boundaries will be chosen only after checking:

- complaint volume by week;
- label coverage in each period;
- publication completeness;
- duplicate narratives across time;
- whether every evaluation label exists in training;
- enough history for theme monitoring.

We will not use a random split merely because it is easier.

## 18. Storage and Git policy

### Must remain outside Git

- downloaded ZIP archive;
- extracted raw complaint files;
- interim complaint tables;
- processed narrative datasets;
- embeddings;
- trained model artifacts;
- large generated reports.

### Can be versioned

- download instructions;
- source URL and archive period;
- schema contracts;
- checksums and non-sensitive metadata;
- code that reproduces transformations;
- configuration files;
- aggregate validation summaries;
- notes and decision logs.

Before downloading, we will confirm `.gitignore` protects all local data paths.

## 19. Failure and stop conditions

Stop the acquisition process if:

- the source domain is not official;
- the server response is incomplete or not a ZIP file;
- free disk space is insufficient;
- the downloaded byte size is zero or unexpectedly different;
- the archive cannot be opened;
- archive members contain unsafe extraction paths;
- the narrative field is absent;
- the covered dates do not match the intended research period;
- the schema cannot be parsed consistently;
- the download would overwrite an existing unverified file.

Stopping is preferable to silently building on an uncertain source.

## 20. Acquisition validation checklist

After the future download, this checklist must be completed:

- [x] Official source URL recorded
- [x] HTTP response succeeded
- [x] Compressed byte size recorded
- [x] SHA-256 calculated
- [x] Archive member list recorded
- [x] Archive member paths validated as safe
- [x] Member uncompressed byte size recorded
- [ ] File encoding inspected
- [ ] Header and delimiter verified
- [ ] Required fields confirmed
- [ ] Sample rows parsed correctly
- [ ] Advertised and actual date coverage compared
- [x] Raw paths confirmed ignored by Git
- [x] Metadata file created with actual values
- [x] No model or result claim made from unverified data

## 21. Decision log

| Decision | Choice | Reason | Status |
|---|---|---|---|
| Authority | Official CFPB FOIA archive | Direct provenance | Confirmed |
| Archive | September 2023–March 2024 | Seven months, manageable size, post-August-2023 taxonomy | Selected candidate |
| Compressed size | 100,880,669 bytes | Server value and downloaded byte count matched | Verified |
| Raw storage | `data/raw/` | Existing repository data-layer convention | Planned |
| Git policy | Exclude all raw complaint data | Privacy, size, and reproducibility | Confirm before download |
| ZIP inspection | Inspect members before extracting | Safety and provenance | Completed |
| Extraction | Extract only after member validation | Preserve milestone boundary | Pending |
| Loading | Schema-first, chunk-capable | Unknown uncompressed size | Planned |
| First target | Still undecided | Requires class and label audit | Pending |
| Temporal split | Preferred | Better historical simulation | Pending audit |

## 22. Interview-ready explanation

### “How did you choose the dataset period?”

> I compared four official CFPB narrative archives using their HTTP metadata. I selected September 2023 through March 2024 because it provides seven months for chronological evaluation and weekly theme monitoring, is still manageable at about 100.9 MB compressed, and falls after the August 2023 complaint-form taxonomy update.

### “Why did you not download the complete historical database?”

> I wanted to establish a reproducible and inspectable pipeline before introducing years of taxonomy changes and much larger storage requirements. One fixed post-update archive is sufficient for the first baseline and retrospective monitoring experiment. Additional periods can later test temporal generalisation.

### “How will you prove which file you used?”

> I will record the official URL, download timestamp, file size, archive members, covered period, and SHA-256 hash. Results will be tied to that snapshot metadata and the experiment configuration.

### “Why inspect the archive before extracting?”

> It confirms the actual members and uncompressed sizes, detects unexpected or unsafe paths, and prevents the pipeline from assuming that a ZIP contains a particular CSV schema.

### “Why use chunked loading?”

> The compressed size does not reveal how large the extracted records will be. Chunking limits peak memory use and lets us validate and aggregate progressively, although cross-chunk duplicates and global counts must still be handled carefully.

### “Why is the target still undecided?”

> Dataset selection and target selection are different decisions. I need actual product and issue counts, label stability, narrative coverage, and temporal coverage before deciding whether Product or Issue is the most defensible first target.

## 23. Implemented acquisition result

The acquisition module was executed on September 28, 2026 and produced the following verified metadata:

| Property | Verified value |
|---|---|
| Download timestamp | `2026-09-28T17:46:13.009137+00:00` |
| Compressed bytes | `100,880,669` |
| SHA-256 | `993747363e52239e4762b804662d7f604f976a139de4f729f613329d3d8c7206` |
| ZIP member count | `1` |
| ZIP member | `CCDB_Export_5_September_2023_through_March_2024.csv` |
| Member compressed bytes | `100,880,397` |
| Member uncompressed bytes | `618,266,146` |
| Member CRC32 | `25d02323` |
| ZIP integrity test | Passed |
| Member path safety check | Passed |

Implementation files:

- `configs/dataset.yaml` — versioned source, expected size, paths, and download controls;
- `src/complaint_intelligence/acquisition.py` — streamed download, disk check, byte validation, hash calculation, ZIP inspection, and metadata writing;
- `tests/test_acquisition.py` — checksum, streaming, ZIP metadata, unsafe path, invalid archive, and disk-control tests.

The generated ZIP and `snapshot_metadata.json` are stored under `data/raw/` and are excluded from Git.

The acquisition and configuration test set passed all 11 tests before download.

## 24. Completion checkpoint

Before downloading, I should be able to explain:

1. why the official FOIA archive is the correct narrative source;
2. why September 2023–March 2024 is the selected candidate;
3. why seven months matters for temporal monitoring;
4. why compressed and extracted sizes differ;
5. why SHA-256 is recorded;
6. why archive members are inspected before extraction;
7. why schema verification happens before transformation code;
8. why raw data remains immutable and outside Git;
9. why chunked loading may be needed;
10. which conditions should stop the acquisition.

The key principle is:

> **A reproducible data-science project identifies and verifies its exact input before it analyses, cleans, or models that input.**

