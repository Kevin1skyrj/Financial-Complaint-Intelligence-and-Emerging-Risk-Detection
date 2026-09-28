# Text Preprocessing and Leakage-Safe Dataset Splits

## Milestone outcome

This milestone creates the frozen datasets that the first supervised classifier will use. It
implements conservative text preparation, strict chronological windows, exact-duplicate
protection, ambiguous-label filtering, and reproducibility metadata. It does **not** fit TF-IDF
or train a model.

Implemented command:

```powershell
$env:PYTHONPATH = "src"
python -m complaint_intelligence.splitting
```

The generated CSV files and JSON report are stored in
`data/processed/classification/` and remain ignored by Git.

## What problem does this solve?

A model evaluation should answer: "How well does a model trained on older complaints classify
genuinely unseen future narratives?" A random split would let nearly identical historical and
future templates appear on both sides, making memorization look like generalization.

The EDA found 104,143 repeat occurrences beyond the first identical narrative. That made split
design a correctness requirement, not an optional improvement.

## Text policy

At this stage the pipeline only:

- removes outer whitespace;
- rejects missing text or product labels;
- computes a SHA-256 hash of the trimmed narrative;
- preserves case, punctuation, numbers, word order, and internal whitespace.

It deliberately does not lowercase, stem, lemmatize, remove stop words, or build a vocabulary.
TF-IDF is a learned transformation: its vocabulary and inverse-document-frequency values must
be fit on the training split only. It will therefore live inside the scikit-learn model pipeline
in the next milestone, not in this data-splitting script.

## Chronological windows

| Split | Date window | Purpose |
|---|---|---|
| Train | 2023-09-01 to 2023-12-31 | Learn vocabulary and model parameters |
| Validation | 2024-01-01 to 2024-02-29 | Select settings without touching final test results |
| Test | 2024-03-01 to 2024-03-31 | One final estimate on the newest held-out month |

The windows are explicit configuration values rather than percentages. The pipeline rejects
overlapping or reversed windows and reports valid records outside the configured period.

## Duplicate and ambiguous-label policy

Processing occurs in chronological split order:

1. Select only records inside the split's date window.
2. Remove any narrative hash already retained in an earlier split.
3. Within that split, remove a hash if identical text maps to multiple product labels.
4. For a repeated hash with one product label, keep its earliest record only.

This gives every final row unique text and guarantees zero hash overlap between train,
validation, and test.

### Why remove conflicting-label hashes?

If the exact same input text is labelled both `Credit card` and `Debt collection`, a text-only
classifier cannot distinguish the two cases. Keeping both creates irreducible label ambiguity
and can reward whichever class is more frequent. The pipeline records how many hashes and rows
were removed rather than resolving the conflict arbitrarily.

### Why remove same-label repetitions?

Repeated complaint templates could heavily weight a few phrases and distort row-level metrics.
Keeping one representative per hash makes the first baseline an evaluation over unique
narratives. The uncollapsed narrative dataset remains available for later operational volume
and emerging-risk analysis, where repetition is meaningful.

### Why purge later duplicates instead of moving them backward?

Moving a March record into training would violate the time boundary. The pipeline keeps strict
calendar windows and removes later text already seen in an earlier retained split. The test set
therefore measures classification on new narrative text during March, which is a deliberately
harder and more honest question than evaluating repeated templates.

## Verified results

The source contained 318,804 usable narrative rows. All rows had a valid date and non-empty
product label, and all fell within the configured windows.

| Split | Window rows | Earlier-split rows removed | Conflicting-label rows removed | Same-label repeats removed | Final rows |
|---|---:|---:|---:|---:|---:|
| Train | 165,611 | 0 | 9,877 | 41,265 | 114,469 |
| Validation | 92,031 | 8,173 | 2,238 | 18,614 | 63,006 |
| Test | 61,162 | 11,455 | 4,560 | 8,276 | 36,871 |

Final exact narrative-hash overlap across splits: **0**.

## Remaining class imbalance

The training split remains dominated by `Credit reporting or other personal consumer reports`:

| Product | Training rows |
|---|---:|
| Credit reporting or other personal consumer reports | 69,276 |
| Debt collection | 11,142 |
| Credit card | 9,318 |
| Checking or savings account | 8,685 |
| Mortgage | 4,011 |
| Student loan | 3,853 |

Accuracy alone would therefore be misleading. The baseline must report macro F1, weighted F1,
per-class precision/recall/F1, a confusion matrix, and a majority-class reference. Balanced
class weights may help, but their effect must be measured rather than assumed.

## Data contracts

Each output row preserves the prepared complaint fields and adds:

- `narrative_hash` — exact trimmed-text identity used for leakage checks;
- `split` — one of `train`, `validation`, or `test`.

The split report records source and output SHA-256 hashes, byte sizes, date ranges, filtering
counts, class distributions, and the zero-overlap assertion. It contains no narrative text.

## What this protects against

- **Temporal leakage:** no future date is placed into an earlier split.
- **Duplicate leakage:** retained narrative hashes never cross split boundaries.
- **Vocabulary leakage:** no TF-IDF vocabulary is learned during splitting.
- **Target ambiguity:** identical text with multiple labels is excluded per split.
- **Silent mutation:** existing outputs require an explicit `--overwrite` flag.
- **Untraceable data:** source and artifact hashes are recorded.

## Limitations

- Hash equality detects exact trimmed-text duplicates, not paraphrases or near duplicates.
- Removing repeats changes the evaluation population from complaint rows to unique narratives.
- Later-window duplicate purging makes the test set focus on previously unseen text.
- Product labels originate from the CFPB taxonomy and may contain annotation noise.
- Only seven months are available, so the test measures one historical month rather than
  long-term deployment drift.
- Split decisions were designed before inspecting model performance, but the fixed archive still
  cannot substitute for a live prospective evaluation.

## Verification

- Complete automated suite: 24 tests passed.
- Tests cover chronology, duplicate purging, conflicting labels, deduplication, privacy-safe
  reporting, invalid dates, outside-window records, overwrite protection, and window validation.
- Full-data split generation completed successfully.
- Cross-split narrative hash overlap was programmatically asserted as zero.
- Python compilation and `git diff --check` passed.

## Interview defense

**Why did you use a chronological split instead of `train_test_split`?**

The intended use is to process future complaints. A random split mixes time periods and can
overstate performance when language or product patterns drift. Training on earlier months and
testing on the newest month better reproduces that direction of time.

**Why is TF-IDF not generated here?**

TF-IDF learns a vocabulary and document frequencies. If it is fit before splitting, information
from validation and test text affects the representation. I keep raw prepared text in the split
files and will fit the vectorizer only through the training pipeline.

**Did deduplication throw away useful volume information?**

Only the classification experiment is deduplicated. The complete narrative dataset remains the
source for weekly volume and emerging-risk analysis because repeated complaints can be an
important operational signal there.

**What exactly does the test result represent?**

It will represent product classification performance on unique March 2024 narratives whose
exact text was not retained in the older training or validation data. It does not represent all
complaints, live production, or population-level consumer harm.

## Next milestone

The next milestone will fit a TF-IDF plus Logistic Regression baseline using `train.csv` only,
use `validation.csv` for limited model selection, and reserve `test.csv` for one final report.
