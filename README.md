# Financial Complaint Intelligence and Emerging Risk Detection

An in-progress data science and NLP project for understanding financial complaint narratives, routing them to the correct category, finding related historical complaints, and identifying complaint themes that are growing unusually quickly.

> **Current status:** The problem definition, architecture, data contract, configuration, package structure, and smoke tests are complete. Data exploration, trained models, evaluation results, semantic retrieval, emerging-risk alerts, dashboards, and RAG features are planned work. No model-performance claims are made yet.

## The problem

Banks, lenders, fintech companies, and other financial institutions receive large numbers of customer complaints through emails, forms, call centres, branches, and regulatory channels. These complaints often arrive as free-form text:

> “My payment was deducted twice, but the additional amount has still not been refunded after several calls.”

A human reviewer must understand the complaint, determine the responsible product and issue, search for similar cases, and decide whether it represents an isolated incident or part of a larger operational problem.

This becomes difficult at scale because:

- complaint descriptions are unstructured and use different words for the same problem;
- manual categorisation can be slow and inconsistent;
- important complaints can be hidden among thousands of routine cases;
- predefined issue labels may not reveal new, more specific complaint themes;
- a rapidly growing problem may remain unnoticed until complaint volume becomes large;
- analysts must search across many historical records to understand whether a case has appeared before.

The project is designed to turn that unstructured complaint stream into structured, searchable, and monitorable intelligence.

## What I am building

The planned system has five connected capabilities.

### 1. Complaint classification

The system will read a public complaint narrative and predict its financial product or issue category.

Example:

```text
Input narrative:
“My EMI was deducted twice and the duplicate payment has not been reversed.”

Planned output:
Predicted product: Consumer loan
Predicted issue: Incorrect payment processing
Model confidence: 0.84
```

The first benchmark will use TF-IDF features with Logistic Regression. This provides a fast and interpretable baseline before more advanced language representations are considered.

### 2. Similar-complaint retrieval

Exact keyword search can miss complaints that describe the same issue using different words. Sentence embeddings and vector similarity will therefore be used to retrieve semantically related historical complaints.

For example, complaints containing “charged twice,” “duplicate EMI,” and “payment debited two times” should be discoverable as related cases even though their wording differs.

This component will help an analyst:

- locate relevant historical examples;
- compare how similar complaints were categorised;
- investigate repeated operational patterns;
- gather evidence before writing a summary or escalating an issue.

### 3. Complaint-theme discovery

Official product and issue labels are useful, but one label may contain several distinct customer problems. The project will cluster complaint embeddings to discover narrower themes directly from the narratives.

Possible discovered themes could include duplicate payment deductions, incorrect credit reporting, delayed loan closure, persistent collection calls, or failed refund processing. These are examples of the intended output, not findings from the dataset yet.

### 4. Emerging-risk detection

After complaints are grouped into themes, the system will track the number of complaints in each theme over time. Statistical and anomaly-detection methods will compare the latest volume with the theme's historical behaviour.

```text
Historical weekly volume for a topic: 8, 11, 9, 13
Current weekly volume:               57

Planned result: unusual increase — analyst investigation required
```

An alert will not claim that misconduct, fraud, or a system failure has occurred. It will indicate that the pattern is unusual enough to deserve investigation.

### 5. Analyst dashboard and grounded summaries

SQL will create analysis-ready tables, and Power BI will present complaint trends, topic growth, detected alerts, and model-performance information.

A later RAG extension will allow an analyst to ask questions such as:

> “Which payment-related complaint themes increased during the last month?”

The assistant will retrieve relevant records and analytical results before generating a cited summary. It will be an evidence-explanation layer, not a replacement for the classifier or the underlying analysis.

## End-to-end flow

```text
Official CFPB complaint data
             |
             v
Source recording and data validation
             |
             v
Narrative filtering, cleaning, and exploratory analysis
             |
             +---------------------------+
             |                           |
             v                           v
TF-IDF classification              Sentence embeddings
             |                           |
             v                           +----------------------+
Product/issue prediction            |                      |
and error analysis                  v                      v
                             Similar-case retrieval   Topic clustering
                                                            |
                                                            v
                                                  Weekly topic volumes
                                                            |
                                                            v
                                                Emerging-risk detection
                                                            |
                          +---------------------------------+------------------+
                          |                                                    |
                          v                                                    v
                  SQL analytical tables                               Power BI dashboard
                                                                               |
                                                                               v
                                                                  Grounded RAG summaries
```

## How the project will be useful

### For complaint operations teams

- Suggest a consistent category for incoming complaints.
- Reduce the time spent searching for similar historical cases.
- Help teams prioritise cases that belong to a rapidly growing theme.
- Provide structured information for routing and investigation.

### For risk and product teams

- Reveal recurring pain points within a financial product.
- Detect changes in complaint patterns earlier than aggregate monthly reporting.
- Compare theme growth across products, periods, companies, or regions where the data permits.
- Support root-cause investigation with representative source complaints.

### For data science and model-risk teams

- Provide class-level performance rather than relying only on overall accuracy.
- Expose rare-category failures and common category confusions.
- Track changes in vocabulary, label distribution, and model confidence over time.
- Keep classification, anomaly detection, and generated summaries separately testable.

### Intended role of the system

The system is a decision-support tool. A human analyst remains responsible for interpreting alerts, validating evidence, and deciding whether an issue requires escalation. It is not intended to make lending, eligibility, pricing, or enforcement decisions.

## Planned technical approach

### Data preparation and exploration

- Validate the schema, dates, identifiers, duplicates, missing values, and label distributions.
- Distinguish complaints without public narratives from genuinely empty text.
- Examine complaint volume, narrative length, category imbalance, and changes over time.
- Define exactly which information would be available when a new complaint arrives.
- Prevent post-complaint outcomes from leaking into model inputs.

### Classification baseline

- Convert narratives into TF-IDF features.
- Train an interpretable Logistic Regression classifier.
- Compare later candidates only against the reproducible baseline.
- Analyse influential terms, misclassified examples, rare categories, and confidence scores.

### Semantic intelligence

- Generate dense sentence embeddings for complaint narratives.
- Retrieve nearest historical complaints using vector similarity.
- Cluster embeddings to discover complaint themes.
- Evaluate whether discovered clusters are coherent, stable, and useful to analysts.

### Temporal monitoring

- Aggregate complaint themes into weekly time series.
- Establish a historical baseline for each theme.
- Detect unusual increases while accounting for normal variation and low-volume noise.
- Rank alerts for review and retain the complaints that support each alert.

### Analytics and reporting

- Build SQL transformations for weekly topic volumes and model outputs.
- Export curated, documented tables for Power BI.
- Present complaint trends, emerging themes, classification performance, and alert evidence.

## Evaluation strategy

Complaint categories are imbalanced, so accuracy alone could hide poor performance on smaller but important classes.

The classification stage will be evaluated using:

- macro and weighted F1;
- per-class precision and recall;
- confusion matrices;
- top-k accuracy;
- probability calibration;
- performance on rare categories;
- qualitative error analysis of incorrectly classified narratives.

The retrieval and clustering stages will require separate evaluation, including relevance checks for retrieved cases and human interpretation of cluster coherence. Emerging-risk experiments will use time-based validation so that future complaint patterns do not leak into historical training data.

No metric will be published until it comes from a documented, reproducible experiment.

## Technology stack

| Area | Planned technologies | Purpose |
|---|---|---|
| Programming | Python | Core data and machine-learning implementation |
| Data processing | Pandas, NumPy | Cleaning, validation, aggregation, and feature preparation |
| Classical ML | Scikit-learn | TF-IDF, Logistic Regression, evaluation, and anomaly-detection experiments |
| Advanced NLP | Sentence Transformers, Hugging Face | Semantic embeddings and model comparisons |
| Data analysis | SQL | Reproducible analytical and dashboard-ready tables |
| Visualisation | Matplotlib, Seaborn, Power BI | EDA, model analysis, and business-facing monitoring |
| Retrieval | Vector similarity search | Finding semantically similar complaint narratives |
| Future GenAI layer | Retrieval-augmented generation | Evidence-grounded summaries with source references |
| Quality | Pytest, Ruff, Git | Testing, code quality, and version control |

Advanced NLP, vector search, Power BI, and RAG are planned technologies and are not implemented yet.

## Data source

The planned source is the official [Consumer Financial Protection Bureau Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/). Relevant fields include the public complaint narrative, product, issue, sub-issue, date received, company, state, submission channel, company response, and timely-response status.

Public narratives are available only when consumers consent to publication and after the CFPB removes personal information. Downloaded records will remain outside Git. See [`data/README.md`](data/README.md) for the initial data contract.

### Important dataset limitation

The CFPB database is not a representative sample of every financial consumer or every problem in the market. Complaint counts can be influenced by awareness of the complaint process, willingness to report, product usage, narrative-publication consent, and other selection effects.

Therefore, this project will describe patterns within submitted CFPB complaints. It will not claim that the detected patterns measure the true prevalence of issues across the entire consumer population.

## Repository structure

```text
.
|-- configs/              # Versioned experiment settings
|-- data/                 # Data contract; local datasets are ignored
|-- docs/                 # Architecture and project decisions
|-- models/               # Generated model artifacts (ignored)
|-- notebooks/            # Numbered exploration and modeling notebooks
|-- powerbi/              # Dashboard specification and future exports
|-- reports/figures/      # Generated charts (ignored)
|-- sql/                  # Analytical queries
|-- src/complaint_intelligence/
|-- tests/
|-- pyproject.toml
`-- requirements.txt
```

## Development roadmap

- [x] Define the problem and intended users
- [x] Design the system architecture and repository structure
- [x] Document the initial data contract and responsible-use boundaries
- [x] Add configuration loading and project smoke tests
- [ ] Download, fingerprint, and profile a reproducible CFPB data snapshot
- [ ] Complete the data-quality audit and exploratory analysis
- [ ] Train the TF-IDF and Logistic Regression baseline
- [ ] Perform class-level evaluation and error analysis
- [ ] Compare baseline models using leakage-safe validation
- [ ] Add probability calibration and confidence analysis
- [ ] Implement semantic embeddings and similar-complaint retrieval
- [ ] Cluster narratives and evaluate discovered complaint themes
- [ ] Detect unusual growth in weekly topic volumes
- [ ] Build SQL transformations and Power BI-ready tables
- [ ] Create the monitoring dashboard
- [ ] Add a cited, retrieval-grounded complaint-summary assistant
- [ ] Document reproducible results, limitations, and future improvements

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

The final command currently prints the project status and configured paths. It does not download data or train a model.

## Responsible-use boundaries

- The project supports complaint triage and analyst investigation; it does not make lending or customer-eligibility decisions.
- Complaint narratives may contain sensitive information and must be handled according to the source terms.
- Protected or post-outcome information must not be introduced as an unjustified prediction feature.
- An emerging-risk alert indicates unusual activity requiring investigation, not confirmed wrongdoing.
- Generated summaries must remain grounded in retrieved evidence and link back to supporting records.
- Human review is required before operational escalation.
- No result or feature will be described as complete until it has been implemented and verified.

## License

Code licensing will be finalised before the first public release. Dataset terms remain governed by the original data provider.
