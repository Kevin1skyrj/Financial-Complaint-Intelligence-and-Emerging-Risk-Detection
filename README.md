# Financial Complaint Intelligence and Emerging Risk Detection

An end-to-end data science and NLP project that converts public CFPB complaint narratives into
classification, retrieval, topic-discovery, temporal-monitoring, SQL analytics, and Power BI
workflows for human investigation.

> **Status:** Version one is implemented and locally validated through the five-page Power BI
> report. The system is a retrospective decision-support prototype, not a deployed financial-risk
> service. Dense neural embeddings, production APIs, automated refresh, and generative summaries
> remain future work.

## Why this project exists

Financial complaints arrive as free-form text. At scale, an analyst must determine the correct
product category, find related historical cases, identify recurring themes, and notice when a theme
is growing unusually quickly.

This project builds those capabilities as separate, testable components:

1. **Product classification** assigns one of 11 CFPB product labels to a complaint narrative.
2. **Similar-complaint retrieval** finds related historical narratives using TF-IDF cosine
   similarity.
3. **Topic discovery** groups narratives into exploratory complaint themes.
4. **Emerging-risk detection** monitors weekly topic share using prior-only robust statistics and
   persistence rules.
5. **Analytics and reporting** expose verified results through SQLite, SQL views, curated exports,
   and a five-page Power BI report.

An alert is an investigation signal. It is not proof of fraud, misconduct, customer harm, or an
institution's quality.

## End-to-end architecture

```text
Official CFPB narrative archive
              |
              v
Download, SHA-256 provenance, extraction, schema inspection
              |
              v
Narrative filtering, quality audit, and conservative preparation
              |
              v
Chronological split + exact-text duplicate isolation
              |
       +------+--------------------+
       |                           |
       v                           v
TF-IDF + Logistic Regression   Historical TF-IDF representation
       |                           |
       v                    +------+----------------+
Held-out evaluation         |                       |
and calibration             v                       v
                     Similar-case retrieval   MiniBatch K-Means topics
                                                     |
                                                     v
                                          Weekly topic-share metrics
                                                     |
                                                     v
                                      Prior-only robust anomaly rules
                                                     |
                               +---------------------+------------------+
                               |                                        |
                               v                                        v
                     SQLite analytical model                  Power BI report
```

## Dataset and leakage controls

The project uses the official CFPB Consumer Complaint Database narrative archive covering
September 2023 through March 2024.

| Data stage | Rows |
|---|---:|
| Source complaints scanned | 945,532 |
| Complaints without a public narrative | 626,728 |
| Narrative complaints retained | 318,804 |
| Unique historical train + validation narratives used to refit models | 177,475 |
| Exact-text-isolated March 2024 test narratives | 36,871 |

Key controls:

- the raw archive is fingerprinted and never silently overwritten;
- learned text transformations are fit only on approved historical data;
- validation and test periods occur after the training period;
- later narratives whose exact text appeared earlier are removed from the later split;
- company-response and other post-arrival outcome fields are excluded from model inputs;
- raw and prepared datasets remain outside Git.

Only 33.72% of source complaints contain a published narrative. Results therefore describe the
selected narrative-bearing CFPB sample, not all consumers or the prevalence of financial problems.

## Verified results

### Classification

The baseline uses a 50,000-feature word/bigram TF-IDF representation and class-weighted Logistic
Regression. Hyperparameters were selected on January-February 2024 validation data, the model was
refit on the combined historical corpus, and March 2024 remained held out for final evaluation.

| Metric | Result |
|---|---:|
| Test rows | 36,871 |
| Accuracy | 0.8242 |
| Balanced accuracy | 0.7578 |
| Macro F1 | 0.6938 |
| Weighted F1 | 0.8318 |
| Expected calibration error | 0.0660 |
| Multiclass log loss | 0.6044 |
| Majority-reference accuracy | 0.6227 |
| Majority-reference macro F1 | 0.0698 |

The gap between majority-reference accuracy and macro F1 demonstrates why class-level evaluation
matters for this imbalanced dataset. The weakest class remains `Debt or credit management`, so the
aggregate score must not be interpreted as uniformly strong performance.

### Similar-complaint retrieval

The first retrieval baseline uses exact cosine similarity over the historical TF-IDF matrix. It is
lexical retrieval, not a neural embedding system.

| Metric | Result |
|---|---:|
| Historical corpus | 177,475 complaints |
| Balanced evaluation queries | 1,100 |
| Precision@5 using product agreement as a proxy | 0.5233 |
| Hit rate@5 | 0.7645 |
| Mean reciprocal rank | 0.6246 |
| Lift over random product agreement | 5.756x |

Product agreement is a weak relevance proxy. A production retrieval system would require
human-judged semantic relevance labels and a comparison with dense embeddings.

### Topic discovery

MiniBatch K-Means candidates with 12, 20, and 30 topics were compared using sampled cosine
silhouette and minimum-cluster-size guardrails. The selected 30-topic model achieved a silhouette
of **0.0490** and assigned all 318,804 narrative complaints.

The low silhouette is reported deliberately: complaint language overlaps substantially, and some
clusters capture templates or legal phrasing. Topics are exploratory groupings requiring human
interpretation, not verified risk categories.

### Emerging-risk monitoring

Each topic is monitored over 30 complete weeks. The detector compares current topic share with the
topic's previous eight weeks using a median/MAD robust z-score. It also requires minimum history,
minimum volume, minimum share increase, and persistence across recent weeks.

| Monitoring result | Value |
|---|---:|
| Topic-week records | 900 |
| Candidate signals | 30 |
| Persistent alerts | 11 |
| Distinct alerted topics | 7 |
| High-priority alerts | 3 |
| Review-priority alerts | 8 |

No labelled real-world incident dataset is available, so alert precision and recall are not
claimed. The alerts validate a reproducible investigation workflow, not real-world causality.

## Power BI report

[`powerbi/Financial_Complaint_Intelligence.pbix`](powerbi/Financial_Complaint_Intelligence.pbix)
contains five pages:

1. **Complaint Overview** - volume trend, KPI cards, alert severity, and denominator guidance.
2. **Emerging Risk Alerts** - persistent-signal evidence and topic-week complaint metadata.
3. **Topic Monitoring** - topic selection, weekly share, historical baseline, and detection fields.
4. **Product & Geography** - product, state, and issue distributions with interpretation limits.
5. **Model Quality** - aggregate metrics, per-product precision/recall/F1, and evaluation scope.

The PBIX imports structured CFPB metadata and derived analytics but excludes consumer narrative
text. It is a local Desktop artifact; Power BI service publication and public sharing are not
configured. See [`powerbi/README.md`](powerbi/README.md) and the
[`final validation note`](notes/12e_powerbi_completion_and_validation.md).

## Technology stack

| Area | Technology | Role in this implementation |
|---|---|---|
| Language | Python 3.10+ | Reproducible batch pipeline and command-line stages |
| Data processing | Pandas, NumPy | Validation, chunked preparation, aggregation, and exports |
| Machine learning | Scikit-learn | TF-IDF, Logistic Regression, retrieval, clustering, and metrics |
| Configuration | YAML | Versioned data, model, clustering, monitoring, and analytics settings |
| Analytics | SQLite and SQL | Relational facts, dimensions, views, indexes, and reconciliation |
| Visualisation | Matplotlib, Seaborn, Power BI | Model diagnostics and analyst-facing reporting |
| Quality | Pytest, Ruff, Git | Automated tests, static checks, and version history |

## Repository structure

```text
.
|-- configs/                         # Versioned pipeline settings
|-- data/                            # Data contract; generated data is Git-ignored
|-- docs/architecture.md             # Compact architecture reference
|-- models/                          # Generated model artifacts; Git-ignored
|-- notes/                           # Step-by-step learning and interview defense
|-- powerbi/
|   |-- Financial_Complaint_Intelligence.pbix
|   `-- README.md
|-- reports/figures/                 # Generated evaluation figures; Git-ignored
|-- sql/                             # Analytics views and reconciliation query
|-- src/complaint_intelligence/      # Pipeline implementation
|-- tests/                           # Automated unit and integration-style tests
|-- pyproject.toml
`-- requirements.txt
```

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Check the local project status:

```powershell
python -m complaint_intelligence
```

## Reproduce the pipeline

The archive acquisition and inspection commands expose help text for their safety options. The
implemented processing stages run in this order:

```powershell
$env:PYTHONPATH = "src"

python -m complaint_intelligence.acquisition --help
python -m complaint_intelligence.inspection --help
python -m complaint_intelligence.preparation
python -m complaint_intelligence.splitting
python -m complaint_intelligence.baseline
python -m complaint_intelligence.evaluation
python -m complaint_intelligence.retrieval
python -m complaint_intelligence.clustering
python -m complaint_intelligence.risk_detection
python -m complaint_intelligence.analytics
```

Generated datasets, models, the SQLite database, and Power BI source CSVs are intentionally
excluded from Git. Their reports record row counts, parameters, hashes, and interpretation notes.

Run quality checks with:

```powershell
python -m pytest -q --basetemp .pytest-tmp
python -m ruff check .
```

## Learning and interview defense

The [`notes/`](notes/README.md) folder documents every milestone in build order. It explains:

- the business problem and responsible-use boundaries;
- dataset provenance, selection bias, and leakage prevention;
- model, retrieval, clustering, and alerting decisions;
- failed experiments and trade-offs;
- exact evaluation results and limitations;
- SQL/Power BI relationships, measures, reconciliation, privacy, and visual QA;
- concise answers to likely interview follow-up questions.

For a focused final review, use the
[`responsible-use note`](notes/14_limitations_and_responsible_ai.md) and
[`interview defense guide`](notes/15_interview_questions.md).

## Responsible-use boundaries

- The system supports human investigation; it does not make lending, pricing, eligibility, or
  enforcement decisions.
- CFPB complaint submissions are not a representative sample of consumers or market prevalence.
- A topic is a machine-generated lexical grouping, not a verified business category.
- An alert indicates an unusual persistent change, not harm, misconduct, fraud, or causation.
- Company and state counts must not be presented as institution-quality or geographic-risk ranks.
- Complaint narratives and generated analytical datasets remain outside the repository.
- Human review is required before interpreting or escalating any result.

## Current completion boundary

Version one is complete as a reproducible local portfolio project through data acquisition,
validation, preparation, leakage-safe modelling, evaluation, retrieval, clustering, temporal
monitoring, SQL analytics, automated tests, and Power BI reporting.

Future improvements include:

- human-labelled semantic-retrieval evaluation and dense-embedding comparison;
- stronger topic-coherence and stability studies across additional time periods;
- backtesting against externally verified incidents where suitable labels exist;
- a production database, API, authentication, monitoring, and scheduled refresh;
- Power BI service deployment only after an explicit audience and embedded-data review;
- an evidence-grounded summary layer only after retrieval faithfulness can be evaluated.

## Data source

Consumer complaint data is governed by the original provider. See the
[CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/)
for source documentation and terms.
