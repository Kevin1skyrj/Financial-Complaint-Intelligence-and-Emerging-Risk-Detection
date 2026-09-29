# TF-IDF and Logistic Regression Baseline

## Milestone outcome

This milestone implements the first complete supervised-learning experiment for predicting the
CFPB product category from complaint narrative text. It uses a TF-IDF representation and
multiclass Logistic Regression inside one scikit-learn pipeline.

Implemented command:

```powershell
$env:PYTHONPATH = "src"
python -m complaint_intelligence.baseline
```

The command performs limited model selection on the validation period, refits the selected
configuration on train plus validation, evaluates the test period once, and saves the fitted
pipeline and aggregate metrics locally. Generated artifacts remain Git-ignored.

## Why start with this baseline?

TF-IDF plus Logistic Regression is a strong first choice for labelled text because it is:

- substantially cheaper and easier to reproduce than a transformer;
- interpretable as a weighted linear decision over words and phrases;
- capable of producing class probabilities;
- fast enough for hundreds of thousands of sparse documents;
- a useful reference that a more complex model must genuinely beat.

The purpose of a baseline is not to be intentionally weak. It establishes a trustworthy minimum
level of performance with a simple, explainable system.

## TF-IDF in plain language

TF-IDF converts text into numbers.

- **Term frequency** increases a feature's value when a word or phrase occurs in a complaint.
- **Inverse document frequency** reduces the value of terms that occur in almost every training
  document and therefore provide little discrimination.
- The result is a sparse matrix: only features present in a document need stored values.

Configured representation:

| Setting | Value | Reason |
|---|---:|---|
| Word n-grams | 1 to 2 | Capture words and short phrases such as `credit report` |
| Minimum document frequency | 3 | Ignore extremely rare features |
| Maximum features | 50,000 | Bound memory and training cost |
| Sublinear term frequency | Enabled | Reduce the influence of repeated terms |
| Stop-word removal | Disabled | Avoid discarding potentially meaningful complaint language prematurely |

The final vocabulary reached the configured limit of 50,000 features. This suggests vocabulary
size is an active capacity constraint and can be tested later, but it was not expanded after
seeing the test score.

## Logistic Regression in plain language

Despite its name, Logistic Regression is a classification algorithm. For each product class it
learns weights for TF-IDF features, converts class scores into probabilities, and selects the
class with the highest probability.

Important settings:

- multiclass optimization with the `lbfgs` solver;
- balanced class weights to reduce domination by the largest product class;
- maximum 250 optimization iterations;
- random seed 42;
- regularization controlled by `C`.

A smaller `C` means stronger regularization and simpler weights. A larger `C` permits the model
to fit the training data more closely.

## Leakage-safe pipeline

TF-IDF and Logistic Regression are stored in the same scikit-learn `Pipeline`. Calling `fit` on
the pipeline first learns the vocabulary from the supplied training text and then fits the
classifier. Validation and test text only call `transform` and cannot add vocabulary.

This prevents a subtle form of leakage where future documents influence inverse-document
frequencies or feature selection.

## Limited model selection

Only two regularization values were compared. All other representation choices were fixed before
the test set was evaluated.

| `C` | Validation accuracy | Balanced accuracy | Macro F1 | Weighted F1 |
|---:|---:|---:|---:|---:|
| 0.5 | 0.8083 | 0.7422 | 0.6712 | 0.8180 |
| 1.0 | **0.8161** | 0.7394 | **0.6787** | **0.8241** |

Selection used validation macro F1, with weighted F1 as a tie-breaker. `C=1.0` was selected.
Balanced accuracy was slightly higher for `C=0.5`, showing that model selection always depends
on the declared objective. Macro F1 was chosen because every product class should influence the
decision rather than letting the dominant class determine it.

## Final training and test protocol

After selection, a new pipeline with `C=1.0` was fit on the combined 177,475 train and validation
rows. Only then was the 36,871-row March test split evaluated.

| Metric | Majority reference | TF-IDF + Logistic Regression |
|---|---:|---:|
| Accuracy | 0.6227 | **0.8242** |
| Balanced accuracy | 0.0909 | **0.7578** |
| Macro F1 | 0.0698 | **0.6938** |
| Weighted F1 | 0.4779 | **0.8318** |

The majority rule always predicts `Credit reporting or other personal consumer reports`. The
large improvement over that reference shows that the model learns class-specific language rather
than only exploiting the dominant label.

## Saved artifacts

- `models/tfidf_logistic_regression.joblib` — fitted vectorizer and classifier;
- `data/processed/classification/baseline_metrics.json` — configuration selection, class metrics,
  confusion matrix, hashes, and evaluation scope;
- `reports/figures/baseline_confusion_matrix.png` — row-normalized final-test confusion matrix.

The model artifact is approximately 6.2 MB. No convergence warnings were produced.

## Limitations

- Word features do not directly understand meaning or paraphrases.
- The 50,000-feature cap may exclude useful rare phrases.
- Balanced weights improve minority attention but can reduce probability calibration.
- Evaluation covers one held-out month from a fixed historical archive.
- Deduplicated evaluation represents unique unseen narratives, not every incoming complaint.
- The product label may sometimes depend on context not stated in the narrative.

## Interview defense

**Why not start with BERT?**

I first needed a reproducible reference with clear leakage controls and low operating cost.
Sparse linear models are strong for many text-classification problems. A transformer is justified
only if it improves the same frozen evaluation without unacceptable latency or complexity.

**Why use macro F1 for selection?**

The classes are highly imbalanced. Macro F1 calculates F1 separately for every class and gives
each class equal weight, so good performance on the dominant credit-reporting category cannot
hide failure on smaller products.

**Why refit after selecting `C`?**

Validation data was no longer needed for model choice after the configuration was frozen. Adding
it to the final fit gives the deployed artifact more historical examples while the untouched test
month still provides an independent evaluation.

**What can you truthfully claim?**

The baseline achieved 0.6938 macro F1 on 36,871 unique, exact-duplicate-isolated March 2024
narratives from the selected CFPB archive. It cannot be claimed as live-production performance.

