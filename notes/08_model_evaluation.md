# Model Evaluation, Error Analysis, and Calibration

## Milestone outcome

This milestone evaluates the frozen TF-IDF and Logistic Regression artifact beyond a single
accuracy number. It measures class-balanced performance, inspects aggregate confusions, and
checks whether predicted confidence corresponds to observed correctness.

Implemented command:

```powershell
$env:PYTHONPATH = "src"
python -m complaint_intelligence.evaluation
```

The evaluation report contains aggregate metrics only. It does not write complaint narratives
or row-level predictions.

## Why several metrics are necessary

| Metric | Question answered | Final test result |
|---|---|---:|
| Accuracy | What share of all predictions was correct? | 0.8242 |
| Balanced accuracy | What is the average recall across classes? | 0.7578 |
| Macro F1 | How well does the model balance precision and recall equally across classes? | 0.6938 |
| Weighted F1 | What is F1 after weighting classes by their support? | 0.8318 |

Weighted F1 is much higher than macro F1 because large classes perform better. Reporting only
accuracy or weighted F1 would hide weak minority-class behavior.

## Per-class results

| Product | Precision | Recall | F1 | Test support |
|---|---:|---:|---:|---:|
| Checking or savings account | 0.7963 | 0.8170 | 0.8065 | 2,339 |
| Credit card | 0.6946 | 0.7971 | 0.7423 | 2,745 |
| Credit reporting or other personal consumer reports | 0.9502 | 0.8446 | 0.8943 | 22,960 |
| Debt collection | 0.6274 | 0.7480 | 0.6824 | 4,457 |
| Debt or credit management | 0.1257 | 0.2400 | 0.1649 | 100 |
| Money transfer, virtual currency, or money service | 0.6499 | 0.7666 | 0.7034 | 874 |
| Mortgage | 0.8081 | 0.9109 | 0.8564 | 1,077 |
| Payday loan, title loan, personal loan, or advance loan | 0.4529 | 0.6983 | 0.5495 | 517 |
| Prepaid card | 0.7467 | 0.7932 | 0.7692 | 353 |
| Student loan | 0.7569 | 0.9053 | 0.8245 | 729 |
| Vehicle loan or lease | 0.5250 | 0.8153 | 0.6387 | 720 |

The strongest F1 scores occur for credit reporting, mortgage, and student loan. The weakest is
`Debt or credit management`, which has only 100 test examples and overlaps linguistically with
debt collection, credit reporting, and account-management complaints. Its low F1 is visible in
macro F1 even though it barely changes overall accuracy.

## Largest confusion pairs

| Actual product | Predicted product | Count | Share of actual class |
|---|---|---:|---:|
| Credit reporting | Debt collection | 1,746 | 7.60% |
| Debt collection | Credit reporting | 736 | 16.51% |
| Credit reporting | Credit card | 684 | 2.98% |
| Credit reporting | Vehicle loan or lease | 366 | 1.59% |
| Checking or savings account | Money transfer service | 236 | 10.09% |

These are aggregate error categories, not evidence that the CFPB labels are wrong. A complaint
can mention debt, a credit report, and a card simultaneously, while the official label selects
one primary product.

## Confusion matrix interpretation

The saved confusion matrix is row-normalized. Every row represents one actual product, and darker
diagonal cells mean higher recall. Row normalization prevents the largest class from visually
overwhelming small classes.

Visible patterns include:

- strong diagonal performance for mortgage, student loan, and credit reporting;
- two-way confusion between debt collection and credit reporting;
- broad confusion for debt or credit management rather than one dominant alternative;
- some overlap among checking accounts, cards, prepaid cards, and money-transfer services.

## Probability calibration

Classification quality and probability quality are different. A prediction can be correct while
its stated confidence is unreliable. Calibration matters if confidence will drive triage queues
or human-review thresholds.

| Calibration metric | Result |
|---|---:|
| Expected calibration error, 10 bins | 0.0660 |
| Multiclass log loss | 0.6044 |
| Multiclass Brier score | 0.2777 |

Expected calibration error compares average confidence with observed accuracy inside confidence
bins. A value of 0 would mean perfect empirical calibration. Here, the reliability diagram lies
mostly above the diagonal, so the model is generally **underconfident**: observed accuracy is
higher than its stated confidence across most bins.

This result does not prove calibration will remain stable in deployment. It is measured on one
historical test month, and bin-based ECE depends on the number and population of bins.

## What error analysis does not establish

- It does not prove a complaint was miscoded.
- It does not establish consumer-harm prevalence.
- It does not measure fairness across protected groups; those attributes are not available here.
- It does not validate a decision threshold for enforcement or adverse consumer action.
- It does not show live drift or production reliability.

## Responsible use

Product predictions can support routing, search, and analyst triage. Low-confidence or sensitive
cases should remain reviewable by humans. The classifier must not make lending, eligibility,
pricing, enforcement, or wrongdoing decisions.

## Verification

- The full test set contains 36,871 unique narratives.
- Model and test-file SHA-256 values are recorded in the evaluation report.
- The evaluation recomputed predictions from the saved model artifact.
- No individual narratives or predictions were exported for error analysis.
- The confusion-matrix and reliability-diagram images were visually inspected.
- The complete automated suite passed without model-code warnings.

## Interview defense

**Why is accuracy not enough?**

The largest class is 62.27% of the test set, so a model that always predicts it already obtains
62.27% accuracy but only 0.0698 macro F1. Macro F1 and per-class results reveal whether smaller
products are actually recognized.

**Why can recall be high while precision is low?**

Balanced class weights make the classifier more willing to predict minority classes. That can
recover more true minority examples, increasing recall, while also creating more false positives
and lowering precision.

**What does ECE 0.066 mean?**

Across ten confidence bins, the weighted average gap between mean confidence and observed
accuracy is about 6.6 percentage points. It is a summary, not a guarantee for every class or
future period.

**What would you improve next?**

I would first inspect privacy-safe representative error groups, test probability calibration on
validation data, and compare a linear SVM or carefully scoped embedding model using the same
frozen temporal evaluation. I would not tune repeatedly against the final test month.

