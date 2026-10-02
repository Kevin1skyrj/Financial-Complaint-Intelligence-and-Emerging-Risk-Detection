# 03 — Technology Stack and Selection Decisions

## 1. Purpose of this note

A technology stack is the collection of languages, libraries, tools, and platforms used to build a system. Choosing a stack is not about listing as many popular tools as possible. Each technology must solve a specific problem in the architecture.

This note explains:

- which technologies are already part of the repository;
- which technologies are planned for later milestones;
- what job each technology performs;
- why it is appropriate for this project;
- which alternatives exist and what their trade-offs are;
- which choices remain deliberately undecided.

The stack will evolve with verified project needs. A planned technology must not be presented as implemented experience until it has actually been used and tested.

## 2. Stack-selection principles

### 2.1 Start with the simplest valid tool

The first solution should establish a correct, reproducible baseline. Complexity is added only when it addresses an observed limitation.

### 2.2 Match the tool to the task

Classification, semantic retrieval, clustering, anomaly detection, SQL transformation, visualisation, and RAG are different tasks. They do not require one universal framework.

### 2.3 Prefer inspectable behaviour

Because the project supports financial complaint analysis, the outputs and errors must be understandable. An interpretable baseline is valuable even if a later model performs better.

### 2.4 Keep experiments reproducible

Dependencies, configurations, random seeds, data snapshots, and artifacts should be versioned or recorded.

### 2.5 Avoid resume-driven architecture

A technology will not be added only because it appears in a job description. It must have a clear role, measurable value, and documented limitation.

## 3. Stack overview

| Layer | Technology | Status | Intended role |
|---|---|---|---|
| Language | Python 3.10+ | Implemented | Core project language |
| Tabular processing | Pandas | Implemented | Data loading, validation, cleaning, and aggregation |
| Numerical operations | NumPy | Implemented | Arrays, numerical transformations, and statistical calculations |
| Classical ML and NLP | Scikit-learn | Implemented | TF-IDF, Logistic Regression, metrics, retrieval, and clustering |
| Experiment interface | JupyterLab | Available | Optional exploration environment; reproducible logic lives in modules |
| Visual analysis | Matplotlib, Seaborn | Implemented | Model diagnostics and evaluation figures |
| Configuration | YAML with PyYAML | Implemented | Versioned experiment settings |
| Testing | Pytest | Implemented | 51 automated validation tests |
| Static quality checks | Ruff | Implemented | Final repository lint validation |
| Packaging | `pyproject.toml`, setuptools | Configured | Installable `src`-layout Python package |
| Version control | Git and GitHub | In use | History, collaboration, and public project evidence |
| Advanced NLP | Sentence Transformers / Hugging Face | Planned | Dense embeddings and later model comparison |
| Similarity search | Sparse TF-IDF cosine similarity | Baseline implemented | Retrieve lexically similar historical complaints |
| Theme discovery | TF-IDF and MiniBatch K-Means | Implemented | Discover exploratory complaint groups |
| Emerging-risk analysis | Prior-only robust statistics and persistence | Implemented | Flag unusual topic-share changes |
| Analytics | SQLite and SQL | Implemented | Reproducible reporting transformations and reconciliation |
| Business reporting | Power BI Desktop | Implemented locally | Five-page interactive analyst report |
| Grounded language layer | RAG with minimal orchestration initially | Future | Source-linked analytical summaries |

The status column distinguishes verified implementation from available dependencies and future
comparisons. Dense neural NLP and the grounded language layer are not current implementation
claims.

## 4. Python

### What it is

Python is a general-purpose programming language with a strong ecosystem for data analysis, machine learning, NLP, testing, and automation.

### Role in this project

Python will coordinate:

- data validation and preparation;
- exploratory analysis;
- feature creation;
- model training and evaluation;
- embedding generation;
- similarity retrieval;
- clustering and anomaly experiments;
- export of analytical datasets.

### Why it was selected

- It supports the full project workflow in one language.
- Pandas, NumPy, Scikit-learn, and Hugging Face have mature Python APIs.
- It is suitable for both notebooks and reusable packages.
- It is widely used in data science, making the project easier to review and reproduce.

### Alternatives

- **R:** excellent for statistics and analysis, but Python provides a more unified route to NLP, packaging, retrieval, and future services for this project.
- **Java:** strong for production systems, but less convenient for rapid data-science experimentation and the selected ML ecosystem.

### Trade-off

Python is not the fastest language for every low-level numerical operation. Most heavy computation here will be performed by optimised library code beneath the Python interface.

## 5. Pandas

### What it is

Pandas is a Python library for working with labelled tabular data through `DataFrame` and `Series` structures.

### Role in this project

- Load complaint records from tabular files.
- Inspect column types and missing values.
- Parse dates and validate identifiers.
- Filter records with usable public narratives.
- Examine product and issue distributions.
- Join predictions, themes, and metadata.
- Aggregate complaints into weekly theme counts.
- Export curated analysis tables.

### Why it was selected

The CFPB data is naturally represented as rows and columns. Pandas provides clear tools for exploration, transformation, grouping, joining, and missing-value analysis.

### Alternatives

- **Polars:** can be faster and more memory-efficient, especially for large data. It may be evaluated if Pandas becomes a measured bottleneck.
- **PySpark:** useful for distributed datasets, but it would introduce infrastructure complexity that is not justified before measuring local resource limits.
- **SQL-only processing:** strong for relational transformations, but text experiments and interactive EDA are easier to combine with Python initially.

### Trade-off

Pandas can consume substantial memory because operations may create copies. Data types, selected columns, chunked reads, and dataset size will be examined before assuming the full snapshot fits comfortably in memory.

## 6. NumPy

### What it is

NumPy provides efficient multidimensional arrays and numerical operations in Python.

### Role in this project

- Support numerical calculations used by Pandas and Scikit-learn.
- Manipulate metric arrays and probability scores.
- Calculate statistical baselines and transformations.
- Handle vector or matrix outputs when needed.

### Why it was selected

NumPy is a foundational dependency across the selected data-science ecosystem. It provides efficient numerical structures and predictable operations.

### Important distinction

Pandas is mainly used for labelled tabular data; NumPy is mainly used for numerical arrays. They often work together but serve different levels of abstraction.

## 7. Scikit-learn

### What it is

Scikit-learn is a machine-learning library that provides preprocessing, feature extraction, models, pipelines, metrics, model selection, clustering, and anomaly-detection tools through consistent APIs.

### Role in this project

- Build TF-IDF text features.
- Train the Logistic Regression baseline.
- Connect preprocessing and modelling through a pipeline.
- Split or validate data using documented strategies.
- Calculate classification metrics and confusion matrices.
- Calibrate probability estimates if required.
- Experiment with clustering and anomaly-detection baselines.

### Why it was selected

- It provides the complete classical-ML baseline workflow.
- Its pipeline abstraction helps prevent training-serving inconsistency.
- Models and transformations follow similar `fit`, `transform`, and `predict` interfaces.
- It is mature, well documented, and appropriate for interview-defensible experiments.

### Alternatives

- **XGBoost or LightGBM:** powerful for structured features, but not necessary for the first sparse-text baseline.
- **PyTorch or TensorFlow:** appropriate for neural models, but unnecessarily complex before establishing a classical benchmark.
- **spaCy:** valuable for linguistic pipelines, but the first classifier does not yet require token-level linguistic components.

### Trade-off

Scikit-learn is not designed to train large transformer models. Advanced neural NLP will require a framework exposed through libraries such as Hugging Face and PyTorch.

## 8. TF-IDF

### What it is

TF-IDF stands for Term Frequency–Inverse Document Frequency. It converts text into numerical features by giving weight to words or phrases that are important within a document but not common across every document.

Simplified intuition:

- a term receives more weight when it appears frequently in one complaint;
- it receives less weight when it appears in nearly every complaint.

### Role in this project

TF-IDF will create the input features for the first complaint classifier.

### Why it was selected

- It is fast and effective for many text-classification problems.
- Features can be inspected as words or n-grams.
- Sparse matrices scale better than dense representations for large vocabularies.
- It creates a strong benchmark before embeddings or transformers.

### Limitations

- It does not deeply understand word order or context.
- Different words with similar meanings remain separate features.
- It may struggle with sarcasm, implicit meaning, or long-range context.
- Vocabulary learned during training cannot fully represent unseen terminology.

### Alternative

Dense sentence embeddings can capture more semantic similarity, but they cost more to generate and are less directly interpretable. The project will compare them only after the baseline is measured.

## 9. Logistic Regression

### What it is

Despite its name, Logistic Regression is commonly used as a classification algorithm. It learns a weighted relationship between input features and class outcomes.

For multiclass complaints, the model produces scores or estimated probabilities for possible categories and selects the highest-ranked class.

### Role in this project

It will be the first supervised model for predicting a complaint product or issue label from TF-IDF features.

### Why it was selected

- It works well with high-dimensional sparse text features.
- It is faster and simpler than deep-learning models.
- Feature weights can help explain which terms influence a category.
- Class weighting can provide an initial response to imbalance.
- It creates an interpretable performance baseline.

### Alternatives

- **Multinomial Naive Bayes:** fast and simple, often useful as an additional reference baseline.
- **Linear Support Vector Machine:** frequently strong for text classification, but standard probability outputs are not directly available and may need calibration.
- **Transformer classifier:** captures richer context but requires more computation, tuning, and careful comparison.

### Trade-off

Logistic Regression creates linear decision boundaries in the feature space. If the relationship between language and categories requires richer contextual interactions, a later model may perform better.

## 10. Scikit-learn Pipeline

### What it is

A Scikit-learn `Pipeline` connects transformations and a model into one fitted object.

Conceptually:

```text
Raw narrative -> TF-IDF transformation -> Logistic Regression -> Prediction
```

### Why it matters

- The TF-IDF vocabulary is fitted only on training data.
- The same fitted transformation is reused for validation and new complaints.
- Model tuning can evaluate the complete workflow.
- Saving the pipeline reduces training-serving skew.

### Main error it prevents

If TF-IDF is fitted on the entire dataset before splitting, evaluation text influences the vocabulary and document-frequency weights. That is data leakage. A correctly used pipeline helps prevent it.

## 11. JupyterLab

### What it is

JupyterLab is an interactive environment combining executable cells, explanations, tables, and charts.

### Role in this project

- Document dataset understanding and EDA.
- Show intermediate reasoning and visual evidence.
- Compare controlled experiments.
- Record observations next to outputs.

### Why it was selected

It is useful for learning and exploratory work where questions evolve while inspecting data.

### Boundary

Notebooks will not become the only implementation. Reusable validation, feature, training, and evaluation logic should move into `src/complaint_intelligence/` and receive automated tests.

### Alternative

Plain Python scripts are easier to automate and review as code, but less convenient for interactive EDA. This project will use notebooks for exploration and modules for reusable behaviour.

## 12. Matplotlib and Seaborn

### What they are

- **Matplotlib** is a foundational Python plotting library with detailed control.
- **Seaborn** provides higher-level statistical visualisations built on Matplotlib.

### Role in this project

- Display label imbalance and missingness.
- Plot narrative-length and complaint-volume distributions.
- Visualise confusion matrices and calibration.
- Show weekly theme behaviour and anomaly signals.
- Produce reproducible figures for reports.

### Why both are included

Seaborn speeds up common statistical plots, while Matplotlib provides lower-level control and underlies many Seaborn figures.

### Boundary

A visually attractive plot is not evidence of a valid conclusion. Every chart needs a defined population, aggregation, axis, time period, and interpretation.

## 13. YAML and PyYAML

### What they are

YAML is a human-readable configuration format. PyYAML allows Python to read YAML files.

### Role in this project

The baseline configuration currently records values such as:

- random seed;
- raw-data path;
- text, target, and date column names;
- test size;
- baseline model name;
- TF-IDF limits;
- class-weighting choice.

### Why configuration is separate from code

- Experiment settings are visible in one place.
- Changes can be reviewed in Git.
- Code does not need to be edited for every experiment.
- A result can reference the configuration that produced it.

### Limitations

YAML does not automatically validate whether every value is meaningful. The application must check required keys, types, ranges, and compatibility.

### Alternatives

- JSON is stricter but less friendly for comments and manual experiment editing.
- TOML is suitable for project configuration and is already used by `pyproject.toml`.
- Command-line arguments are useful for overrides but can become difficult to reproduce if they are not recorded.

## 14. `pyproject.toml` and the `src` layout

### `pyproject.toml`

This file defines the Python project, build system, supported Python version, package discovery, test paths, and Ruff settings.

### `src` layout

The reusable package lives inside `src/complaint_intelligence/` rather than directly at the repository root.

### Why this structure was selected

- It separates importable project code from notebooks and repository files.
- It reduces accidental imports from the working directory.
- It encourages the project to behave like an installed package.
- It makes testing reusable logic more realistic.

## 15. Pytest

### What it is

Pytest is a Python testing framework.

### Role in this project

- Verify configuration loading.
- Test schema validation and cleaning rules later.
- Test that data transformations behave consistently.
- Check metric and alert calculations on controlled examples.
- Prevent regressions when components change.

### Why it was selected

It has readable test syntax, useful fixtures, clear failure output, and broad adoption in Python projects.

### What tests cannot prove

Passing code tests do not prove that a model is useful, unbiased, or statistically valid. Model evaluation, data review, and domain interpretation remain separate responsibilities.

## 16. Ruff

### What it is

Ruff is a fast Python linter and formatter.

### Role in this project

- Detect common code-quality problems.
- Enforce consistent style.
- reduce avoidable review noise.

### Why it was selected

It is fast and can replace several separate style tools for a small project.

### Boundary

Linting checks code structure and style; it does not validate data-science reasoning or model correctness.

## 17. Git and GitHub

### Role in this project

- Record small, meaningful milestones.
- Preserve the reasoning and code history.
- Make changes reviewable.
- Link documentation to the implementation state.
- Provide a public project artifact for the resume.

### Why commit history matters

A sequence of documented milestones is stronger evidence of genuine development than one final upload. It shows how the problem, experiments, and decisions evolved.

### Data rule

Raw complaints, processed datasets, large embeddings, and generated model artifacts should not be committed merely because Git is available. Git tracks the code and documentation needed to reproduce them.

## 18. Sentence Transformers and Hugging Face

### Status

Planned, not yet installed or implemented.

### What they are

- **Hugging Face Transformers** provides pretrained transformer models and tooling.
- **Sentence Transformers** provides models designed to convert sentences or documents into dense vectors useful for semantic similarity.

### Role in this project

- Generate complaint embeddings.
- Retrieve semantically similar narratives.
- Provide representations for clustering.
- Potentially compare an advanced classifier with the classical baseline later.

### Why they are planned

TF-IDF relies heavily on shared vocabulary. Dense embeddings can place differently worded but semantically related complaints closer together.

### Alternatives

- Hosted embedding APIs may provide strong representations but introduce cost, external data transfer, credentials, and reproducibility concerns.
- Training an embedding model from scratch is computationally expensive and unjustified for the first version.
- Traditional word embeddings such as Word2Vec require a method to combine word vectors into complaint-level representations and may capture less sentence-level context.

### Trade-offs

- More compute and memory than TF-IDF.
- Model choice can strongly affect retrieval quality.
- Dense similarity is less directly interpretable.
- General-purpose embeddings may misunderstand domain-specific financial language.
- Version and licensing information must be recorded.

No specific pretrained model will be selected until dataset language, size, hardware constraints, and evaluation design are understood.

## 19. Similarity search baseline and a future dense-vector index

### First approach

The implemented baseline compares a query's sparse TF-IDF vector with the stored historical TF-IDF
matrix using exact cosine similarity. This provides an inspectable reference result before any
dense-embedding or approximate-index comparison.

### Why not select a vector database immediately?

A vector database or approximate nearest-neighbour index is valuable when scale or latency requires it. Selecting one before measuring dataset size, memory usage, and search speed would be premature.

### Possible later options

- **FAISS:** efficient local vector indexing and similarity search.
- **HNSW-based libraries:** fast approximate nearest-neighbour search.
- **PostgreSQL with pgvector:** combines relational metadata filtering with vector search.
- **Managed vector database:** operational convenience at the cost of an external service, cost, and additional governance.

### Decision rule

Start with correct exact retrieval, measure it, and introduce an index only if scale or latency justifies the added complexity.

## 20. Clustering technology

### Status

The clustering algorithm has not been selected.

### Initial candidates

- **K-Means:** scalable and easy to understand, but requires choosing the number of clusters and assumes compact groups.
- **MiniBatch K-Means:** more scalable variation for larger datasets.
- **HDBSCAN:** can discover variable-density clusters and mark noise, but adds a dependency and produces parameters that require careful interpretation.

### Why the decision is deferred

The correct choice depends on embedding quality, dataset size, theme shape, noise, stability, and business interpretability. We will not choose an algorithm only because it is popular.

### Evaluation need

Internal scores alone do not prove business meaning. Representative complaints, cluster coherence, stability, and analyst interpretation must also be examined.

## 21. Emerging-risk detection technology

### Status

The final method has not been selected.

### Planned progression

1. Build weekly complaint counts for each valid theme.
2. Create simple reference signals such as recent change and historical z-scores where assumptions permit.
3. Account for minimum volume, trend, and possible seasonality.
4. Compare more advanced anomaly methods only when the baseline limitations are clear.

### Candidate approaches

- rolling mean and standard deviation rules;
- robust median and median absolute deviation;
- exponentially weighted baselines;
- change-point detection;
- Scikit-learn anomaly models such as Isolation Forest, if feature design supports them.

### Why statistical baselines come first

An analyst should understand why an alert fired. A simple, transparent baseline also provides a benchmark for deciding whether a more complex detector improves usefulness.

### Important warning

Isolation Forest or any other algorithm does not automatically make the result an “AI risk detector.” The time-series representation, evaluation procedure, alert threshold, and false-alert analysis are more important than the algorithm name.

## 22. SQL

### What it is

SQL is a language for defining, transforming, joining, filtering, and aggregating relational data.

### Role in this project

- Create weekly complaint-volume tables.
- Combine predictions, theme assignments, and metadata.
- Define reusable dashboard views.
- Calculate product, issue, time, and geographic summaries.
- Make analytical logic inspectable outside a notebook.

### Why it was selected

SQL is widely used by financial analytics teams and is well suited to reproducible aggregation and reporting logic.

### Database choice

No final database engine has been selected. Early experiments may use local files or an embedded analytical database. A database will be chosen after data size, query needs, portability, and Power BI connectivity are assessed.

Possible options include:

- **DuckDB:** convenient local analytics over files with minimal setup.
- **PostgreSQL:** stronger multi-user relational system and optional `pgvector` extension.
- **SQLite:** simple local storage, but less suited to some analytical and vector requirements.

### Trade-off

Duplicating the same transformation in Pandas and SQL can create inconsistent results. One authoritative implementation and reconciliation tests should be defined for each production table.

## 23. Power BI

### What it is

Power BI is a business-intelligence platform for interactive data models, reports, and dashboards.

### Role in this project

- Show complaint volume and category trends.
- Display emerging themes and historical context.
- Support filtering by time and relevant metadata.
- Present model quality and confidence information.
- Allow drill-through from an alert to supporting records where appropriate.

### Why it is used

The system's users need interpretable views, not only notebook outputs. Power BI also reflects how analytical results are often communicated in organisations.

### Boundary

Power BI should consume curated, documented tables. Complex data-cleaning or model logic should not be hidden only inside dashboard calculations.

### Alternative

Tableau or a custom Streamlit dashboard could present similar information. Power BI was used for
the completed five-page local business-reporting layer, while a lightweight web interface remains
an optional future model demonstration.

## 24. Retrieval-Augmented Generation

### What it is

Retrieval-Augmented Generation, or RAG, first retrieves relevant evidence and then asks a language model to answer using that evidence.

```text
Analyst question
      |
      v
Retrieve relevant complaints and calculated results
      |
      v
Construct evidence-grounded prompt
      |
      v
Generate answer with source references
```

### Role in this project

A later RAG layer may summarise emerging themes, representative complaints, and analytical results.

### Why it comes last

RAG depends on reliable retrieval, clean metadata, and traceable evidence. Without these foundations, a fluent answer can still be unsupported or misleading.

### Framework decision

No LangChain, LlamaIndex, or other orchestration framework is selected yet. The first grounded flow should be implemented with minimal transparent components. A framework will be added only if it clearly simplifies retrieval, evaluation, tracing, or provider integration.

### Risks

- hallucinated conclusions;
- missing or incorrect citations;
- relevant evidence omitted during retrieval;
- prompt injection inside retrieved text;
- private text sent to an external service;
- generated language interpreted as verified fact.

## 25. Technologies intentionally not selected yet

The following decisions require evidence from later milestones:

| Decision | Evidence needed first |
|---|---|
| First final target label | Label counts, hierarchy, quality, and stability |
| Embedding model | Language, retrieval task, hardware, licensing, and evaluation set |
| Clustering algorithm | Embedding geometry, scale, noise, coherence, and stability |
| Anomaly detector | Theme histories, seasonality, false-alert cost, and baseline results |
| Database engine | Data size, query patterns, Power BI needs, and vector strategy |
| Vector index | Exact-search latency, memory, scale, and filtering needs |
| RAG model/provider | Privacy, cost, evaluation, deployment, and evidence requirements |
| Deployment platform | Interface, workload, budget, security, and monitoring needs |

Deferring these choices is good engineering because it avoids building around unsupported assumptions.

## 26. Dependency strategy

The project currently declares only the tools needed for the initial data, baseline, visualisation, testing, and quality workflow.

Advanced dependencies will be added at the milestone where they are first used. This keeps setup lighter and prevents the repository from claiming unused technologies.

Version ranges are bounded to reduce unexpected breaking changes while allowing compatible updates. Exact environment locking may be added when reproducible experiments begin.

## 27. How the tools connect

```text
JupyterLab
   |
   | explores and documents
   v
Pandas + NumPy -------------------------+
   |                                    |
   | prepare tabular data               | aggregate time signals
   v                                    v
Scikit-learn Pipeline              Statistical/anomaly methods
TF-IDF -> Logistic Regression            |
   |                                      |
   v                                      v
Predictions and metrics            Emerging-theme signals

Sentence Transformers / Hugging Face (later)
   |
   v
Embeddings -> retrieval + clustering
   |
   v
SQL analytical tables -> Power BI
   |
   v
Evidence retrieval -> future RAG summary

PyYAML config + Pytest + Ruff + Git support every stage.
```

## 28. Interview-ready explanation

### “Why did you choose Python?”

> Python lets me use one mature ecosystem for data preparation, classical machine learning, NLP, evaluation, and automation. It also supports both exploratory notebooks and reusable packaged code.

### “Why did you choose TF-IDF and Logistic Regression?”

> I need a fast, interpretable, and reproducible baseline before using complex models. TF-IDF works well for sparse text features, and Logistic Regression handles high-dimensional sparse inputs while allowing class weighting and inspection of feature influence. A later model must demonstrate measurable value over this baseline.

### “Why not start with BERT or another transformer?”

> A transformer increases compute and tuning complexity before I understand the dataset and baseline errors. I will first identify where TF-IDF fails, then evaluate whether embeddings or a transformer improve those specific limitations.

### “Why use both Pandas and SQL?”

> Pandas supports interactive cleaning, EDA, and Python model preparation. SQL provides explicit, reusable transformations for analytical tables and dashboards. I will avoid duplicating business logic without reconciliation.

### “Why use Power BI if you already have Python plots?”

> Python plots are best for reproducible EDA and model diagnostics. Power BI is intended for interactive analyst views, filtering, trend monitoring, and drill-through over curated outputs.

### “Why not choose a vector database now?”

> I first need to measure dataset scale and exact-search performance. Exact cosine similarity gives me a correctness baseline. I will introduce FAISS, pgvector, or another index only if latency, memory, or filtering requirements justify it.

### “Why is RAG the final stage?”

> RAG can explain retrieved evidence, but it cannot fix poor data, weak retrieval, unstable themes, or invalid anomaly signals. I need traceable evidence and evaluated retrieval before generating summaries.

### “How are you controlling dependency complexity?”

> I add a dependency only when its milestone begins and its role is clear. The current environment covers the verified sparse retrieval, clustering, monitoring, SQL, and reporting workflow. Dense neural NLP, approximate vector indexing, and RAG remain future dependencies until they have a justified evaluation plan.

## 29. Completion checkpoint

Before moving to dataset understanding, I should be able to explain:

1. why Pandas and NumPy are related but different;
2. why Scikit-learn is appropriate for the baseline;
3. how TF-IDF converts text into model features;
4. why Logistic Regression is a classifier despite its name;
5. how a Pipeline helps prevent leakage and preprocessing mismatch;
6. why notebooks and reusable modules have separate roles;
7. why embeddings are useful for semantic similarity;
8. why clustering and anomaly algorithms remain undecided;
9. why SQL and Power BI are downstream of verified analysis;
10. why RAG requires reliable retrieval first.

The key stack-selection rule is:

> **Use the simplest technology that correctly solves the current problem, measure its limitations, and add complexity only when evidence justifies it.**

