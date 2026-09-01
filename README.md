# Financial Complaint Intelligence and Emerging Risk Detection

An in-progress data science system for classifying financial complaint narratives, retrieving similar historical cases, and detecting emerging complaint themes before they become widespread operational risks.

> **Project status:** Initial repository scaffold. Dataset exploration, trained models, evaluation results, dashboard, and retrieval features are planned work and are not yet claimed as complete.

## Problem statement

Financial institutions receive large volumes of unstructured customer complaints. Manual review alone makes it difficult to route cases consistently and notice rapidly growing issues early.

This project will answer three questions:

1. What product and issue does a complaint concern?
2. Which historical complaints are most similar?
3. Is a complaint theme growing unusually quickly over time?

## Planned system

```text
CFPB complaint data
        |
        v
Data validation and text cleaning
        |
        +--------------------+
        |                    |
        v                    v
TF-IDF classification   Sentence embeddings
        |                    |
        v                    v
Product/issue routing   Similar-case retrieval and clustering
                             |
                             v
                    Weekly topic-volume signals
                             |
                             v
                    Emerging-risk alerts
```

## Why this project

The work combines practical NLP with problems relevant to a financial-services team:

- multiclass text classification;
- imbalanced-label evaluation using macro F1 and per-class recall;
- semantic similarity and clustering;
- time-based anomaly detection for emerging issues;
- SQL analysis and Power BI-ready outputs;
- explainability, error analysis, drift, and data-quality checks;
- a later grounded RAG layer for cited summaries of retrieved complaints.

## Data source

The planned source is the official [Consumer Financial Protection Bureau Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/). Public narratives are published only when consumers consent and after personal information is removed.

The database is not a representative sample of all consumers. Results will therefore describe patterns in submitted CFPB complaints, not the prevalence of problems across the entire population.

Downloaded data is intentionally excluded from Git. See [`data/README.md`](data/README.md) for the expected fields and data-handling rules.

## Repository structure

```text
.
|-- configs/              # Versioned experiment settings
|-- data/                 # Data contract; local data is ignored
|-- docs/                 # Architecture and project decisions
|-- models/               # Generated model artifacts (ignored)
|-- notebooks/            # Numbered exploration and modeling notebooks
|-- powerbi/              # Dashboard specification and exports later
|-- reports/figures/      # Generated charts (ignored)
|-- sql/                  # Analytical queries
|-- src/complaint_intelligence/
|-- tests/
|-- pyproject.toml
`-- requirements.txt
```

## Roadmap

- [x] Define the problem, architecture, data contract, and repository structure
- [x] Add configuration loading and project smoke tests
- [ ] Download and profile a reproducible CFPB data snapshot
- [ ] Establish a TF-IDF + Logistic Regression baseline
- [ ] Compare baseline models with leakage-safe validation
- [ ] Perform class-level error analysis and probability calibration
- [ ] Add embeddings, similar-case retrieval, and topic clustering
- [ ] Detect unusual growth in weekly topic volumes
- [ ] Export curated tables for a Power BI dashboard
- [ ] Add a cited, retrieval-grounded complaint-summary assistant

## Local setup

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest
python -m complaint_intelligence
```

The last command prints the project status and configured paths. It does not train a model yet.

## Evaluation plan

Accuracy alone is unsuitable because complaint categories are imbalanced. Planned evaluation includes macro and weighted F1, per-class precision/recall, confusion matrices, top-k accuracy, probability calibration, and performance on rare categories. Time-based validation will be used for emerging-risk experiments.

## Responsible-use boundaries

- The system supports complaint triage and analyst investigation; it does not make lending or eligibility decisions.
- Complaint narratives may contain sensitive text and must be handled according to the source terms.
- Generated summaries must link back to retrieved source records and must not invent evidence.
- No performance number will be reported until a reproducible experiment produces it.

## License

Code licensing will be finalized before the first public release. Dataset terms remain governed by the original data provider.

