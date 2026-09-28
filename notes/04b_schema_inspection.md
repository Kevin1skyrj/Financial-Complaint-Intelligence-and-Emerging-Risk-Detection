# 04B — Safe Extraction and Schema Inspection

## 1. Purpose of this milestone

This milestone converts a verified ZIP archive into a verified raw CSV and answers the first factual questions about the file:

- Can the expected member be extracted safely?
- Does the extracted byte count match ZIP metadata?
- What encoding and delimiter does the file use?
- Which columns are actually present?
- How many rows and time periods are included?
- Are identifiers and dates structurally usable?
- How much narrative text is available?
- How imbalanced are the unfiltered product and issue labels?

This is still not data cleaning or modelling. The CSV was scanned without creating a processed modelling dataset.

## 2. Implementation

The milestone adds:

- `src/complaint_intelligence/inspection.py`;
- extraction and inspection settings in `configs/dataset.yaml`;
- `tests/test_inspection.py`.

The module performs the following flow:

```text
Load snapshot metadata
        ↓
Verify archive filename, size, and SHA-256 again
        ↓
Locate one explicitly configured ZIP member
        ↓
Validate the member path
        ↓
Check free disk space
        ↓
Extract through a temporary .part file
        ↓
Verify extracted byte count and calculate SHA-256
        ↓
Inspect encoding, delimiter, header, and first-record width
        ↓
Validate required columns
        ↓
Scan the CSV in 50,000-row chunks
        ↓
Write local extraction metadata and schema report
```

## 3. Why re-verify the archive?

The archive was verified during acquisition, but extraction can happen later. The file could have been moved, replaced, truncated, or modified between those steps.

Before extraction, the implementation checks:

- archive filename;
- compressed byte count;
- SHA-256 against `snapshot_metadata.json`.

This creates a chain of evidence:

```text
Official URL
    ↓
Verified ZIP hash
    ↓
Verified archive member
    ↓
Verified extracted CSV hash
    ↓
Schema report
```

## 4. Extraction safety

The implementation does not perform unrestricted extraction.

It:

- extracts only the explicitly configured member;
- rejects absolute paths;
- rejects `..` parent-directory traversal;
- rejects drive-qualified archive paths;
- refuses to overwrite an existing extracted CSV unless explicitly requested;
- writes first to a `.part` file;
- deletes the temporary file if extraction fails;
- checks available disk space before writing;
- compares extracted bytes with ZIP member metadata.

This prevents a malformed archive member from writing outside the intended data directory and avoids treating incomplete extraction as a successful dataset.

## 5. Verified file identity

### Source archive

```text
Filename: CCDB_Export_5_September_2023_through_March_2024.zip
Bytes:    100,880,669
SHA-256:  993747363e52239e4762b804662d7f604f976a139de4f729f613329d3d8c7206
```

### Extracted CSV

```text
Filename: CCDB_Export_5_September_2023_through_March_2024.csv
Bytes:    618,266,146
SHA-256:  7a8645f6f602762fcf8cdbf01005aaad9a5834debc9cab549ff94b6b128b1ab0
CRC32:    25d02323
```

The extracted byte count and CRC32 agree with the ZIP member metadata.

## 6. Verified text format

| Property | Observed value |
|---|---|
| Encoding used successfully | `utf-8-sig` |
| UTF-8 BOM present | No |
| Configured delimiter | Comma |
| Detected delimiter | Comma |
| Header width | 16 columns |
| First record width | 16 fields |
| First record matches header | Yes |

`utf-8-sig` can decode ordinary UTF-8 whether or not a BOM is present, so it is acceptable for this file.

## 7. Verified archived schema

The CSV contains 16 columns:

1. `Date received`
2. `Product`
3. `Sub-product`
4. `Issue`
5. `Sub-issue`
6. `Consumer complaint narrative`
7. `Company public response`
8. `Company`
9. `State`
10. `ZIP code`
11. `Tags`
12. `Submitted via`
13. `Date sent to company`
14. `Company response to consumer`
15. `Timely response?`
16. `Complaint ID`

All five fields required for the first NLP investigation are present:

- `Complaint ID`;
- `Date received`;
- `Product`;
- `Issue`;
- `Consumer complaint narrative`.

## 8. Chunked scan results

The file was scanned in chunks of 50,000 rows.

| Measurement | Result |
|---|---:|
| Total rows | 945,532 |
| Chunks processed | 19 |
| Columns | 16 |
| Unique non-null complaint IDs | 945,532 |
| Duplicate complaint IDs | 0 |
| Invalid or missing received dates | 0 |
| Earliest received date | 2023-09-01 |
| Latest received date | 2024-03-31 |
| Unique products | 11 |
| Unique issues | 88 |

The actual received-date range exactly matches the archive's advertised September 2023–March 2024 period.

## 9. Required-field missingness

| Field | Missing or empty rows | Percentage of all rows |
|---|---:|---:|
| `Complaint ID` | 0 | 0.00% |
| `Date received` | 0 | 0.00% |
| `Product` | 0 | 0.00% |
| `Issue` | 1 | approximately 0.00% |
| `Consumer complaint narrative` | 626,728 | 66.28% |

Usable non-empty narrative rows before any other filtering:

```text
945,532 - 626,728 = 318,804 rows
```

Narrative availability:

```text
318,804 / 945,532 = 33.72%
```

This confirms that the modelling population will be a selected subset of the archive, not all archived complaints.

## 10. Product imbalance before narrative filtering

| Product | Rows | Share of all rows |
|---|---:|---:|
| Credit reporting or other personal consumer reports | 781,459 | 82.65% |
| Debt collection | 50,752 | 5.37% |
| Credit card | 36,975 | 3.91% |
| Checking or savings account | 27,319 | 2.89% |
| Mortgage | 12,597 | 1.33% |
| Student loan | 10,629 | 1.12% |
| Money transfer, virtual currency, or money service | 8,789 | 0.93% |
| Vehicle loan or lease | 7,306 | 0.77% |
| Payday loan, title loan, personal loan, or advance loan | 4,777 | 0.51% |
| Prepaid card | 4,028 | 0.43% |
| Debt or credit management | 901 | 0.10% |

These percentages describe all archive rows. They are not yet the training distribution because narrative availability can differ by product.

## 11. Issue imbalance before narrative filtering

The three largest issue labels are:

| Issue | Rows |
|---|---:|
| Incorrect information on your report | 386,498 |
| Improper use of your report | 230,580 |
| Problem with a company's investigation into an existing problem | 164,692 |

Together, these credit-reporting-related issues dominate the archive. This is consistent with the product imbalance and shows why raw accuracy would be a weak evaluation metric.

The scan found 88 unique issue labels, but issue prediction feasibility must be measured again after filtering to usable narratives and examining product–issue relationships.

## 12. What these results establish

We now know that:

- the selected archive is authentic relative to recorded acquisition metadata;
- the expected single CSV can be extracted safely;
- the file is parseable as comma-delimited UTF-8;
- the required NLP fields exist;
- identifiers are unique and complete;
- received dates are complete and cover the advertised period;
- only about one-third of records contain usable narrative text;
- the unfiltered archive is extremely dominated by credit-reporting complaints;
- class imbalance must be handled explicitly.

## 13. What these results do not establish

We do not yet know:

- narrative availability by product and issue;
- narrative length distribution;
- exact duplicate or near-duplicate narrative counts;
- whether narratives contain template-heavy language;
- weekly completeness and volume behaviour;
- product balance after narrative filtering;
- whether Product is too easily inferred from explicit product words;
- which labels appear in every temporal split;
- which target scope is most defensible;
- whether any model performs well.

Those questions belong to the cleaning and EDA milestone.

## 14. Why we did not store example narratives

The schema report records structure and aggregate counts but does not copy complaint narratives into version-controlled output.

Even though the archive is public, unnecessary reproduction of narrative text would:

- add no value to schema validation;
- increase privacy and handling concerns;
- make reports larger;
- risk committing raw content accidentally.

Future examples should use complaint IDs, redacted excerpts only where necessary, or synthetic examples for documentation.

## 15. Implications for the modelling plan

### Narrative filtering is unavoidable

The first NLP dataset can contain at most 318,804 rows before other quality rules.

### Product imbalance may change after filtering

We must calculate product counts specifically among narrative-bearing records. We must not reuse the full-archive distribution as the modelling distribution.

### Random splitting is risky

The archive covers seven chronological months. We should inspect weekly label coverage and duplicates before selecting time boundaries.

### Accuracy will be insufficient

Because one product holds 82.65% of all rows before filtering, a majority-class strategy could look strong by accuracy while being useless on smaller products.

### Issue prediction is likely harder

There are 88 issue labels before filtering, and the top three dominate. Issue classification should not be the first target without a controlled scope and sufficient examples per class.

## 16. Tests and verification

The combined configuration, acquisition, and inspection suite passed:

```text
17 passed
```

The tests cover:

- archive identity verification;
- checksum mismatch rejection;
- streamed safe extraction;
- overwrite protection;
- encoding and delimiter inspection;
- required-column validation;
- chunked row counting;
- valid and invalid date handling;
- empty narrative counting;
- label counting;
- malformed metadata rejection;
- unsafe ZIP-member rejection.

Generated local files are ignored by Git:

- extracted CSV;
- extraction metadata;
- schema report.

## 17. Interview-ready explanation

### “How did you verify the raw dataset?”

> I rechecked the ZIP filename, byte count, and SHA-256 against acquisition metadata before extraction. I extracted only the configured member through a temporary file, validated its path and exact byte count, calculated the CSV hash, inspected encoding and delimiter, confirmed required columns, and scanned the complete file in chunks.

### “Why did you scan in chunks?”

> The extracted CSV is about 618 MB. Chunking limits peak memory and still lets me aggregate row counts, missingness, identifiers, dates, and label frequencies across the complete file.

### “What was the most important data-quality finding?”

> Only 318,804 of 945,532 records contain non-empty complaint narratives, so the NLP population is about 33.72% of the archive. Narrative-bearing complaints are a selected subset and need their own class-distribution analysis.

### “Why can accuracy be misleading?”

> Before narrative filtering, 82.65% of records belong to credit reporting or other personal consumer reports. A model biased toward that category could achieve high accuracy while failing most smaller products, so I need macro and per-class metrics.

### “Did the archive match its advertised period?”

> Yes. The earliest received date was September 1, 2023 and the latest was March 31, 2024, with no invalid or missing received dates.

### “Did you find duplicate records?”

> I found no duplicate Complaint IDs. That does not rule out different IDs with identical or near-identical narrative text; narrative duplication will be measured during EDA before splitting.

## 18. Completion checkpoint

Before starting cleaning and EDA, I should understand:

1. why archive identity was verified twice;
2. how safe extraction differs from unrestricted unzip;
3. why the CSV was scanned in chunks;
4. why 945,532 source rows do not mean 945,532 modelling rows;
5. why narrative availability creates selection bias;
6. why full-archive and narrative-only class distributions differ;
7. why no duplicate IDs does not rule out duplicate narratives;
8. why target selection remains pending;
9. why accuracy alone would be misleading;
10. which questions must be answered in EDA.

The key conclusion is:

> **The source file is structurally valid and reproducible, but narrative availability and severe class imbalance must be analysed before defining the modelling dataset.**

