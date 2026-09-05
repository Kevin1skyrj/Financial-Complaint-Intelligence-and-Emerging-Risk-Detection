# 02 — System Architecture

## 1. Purpose of this note

System architecture describes how the project's parts connect, what information moves between them, and where each responsibility begins and ends.

This note answers:

- What are the major components?
- What does each component receive and produce?
- Which parts run during experimentation, batch analysis, and future inference?
- Which artifacts must be stored and versioned?
- Where can data leakage or incorrect assumptions enter?
- Why is the system divided into separate pipelines?
- What will be built first, and what is intentionally deferred?

This is a logical architecture for a portfolio project. It does not claim that a production cloud platform or real-time service has already been deployed.

## 2. Architecture in one sentence

The system converts a reproducible snapshot of public CFPB complaints into validated records, classification predictions, semantic representations, complaint themes, time-based risk signals, and analyst-facing outputs while keeping every stage independently testable.

## 3. Why architecture matters in a data-science project

A notebook can train a model, but a complete data-science system must also answer:

- Where did the data come from?
- Which transformations were applied?
- Which model and configuration produced a prediction?
- Can an experiment be repeated?
- Can a reviewer inspect errors and supporting records?
- Can one component change without silently breaking another?
- Are future data or post-outcome fields leaking into the model?

Architecture provides these boundaries. It prevents the project from becoming one large notebook containing unrelated data cleaning, modelling, charts, and generated text.

## 4. Architectural principles

### 4.1 Separate responsibilities

Data validation, classification, retrieval, clustering, temporal monitoring, reporting, and RAG solve different problems. Each component should have a defined input, output, and evaluation method.

### 4.2 Build from simple to advanced

The first working path will be data validation followed by an interpretable TF-IDF and Logistic Regression baseline. Embeddings, clustering, anomaly detection, dashboards, and RAG will be added only after their dependencies are reliable.

### 4.3 Preserve reproducibility

Dataset identity, configurations, code version, random seeds, and generated artifacts must be traceable. A reported result should be reproducible from documented inputs.

### 4.4 Keep raw data immutable

Raw downloaded data should not be manually edited. Cleaning creates new interim or processed artifacts so that every transformation can be repeated.

### 4.5 Make uncertainty and evidence visible

Predictions require confidence information, alerts require historical context, clusters require representative complaints, and generated summaries require source references.

### 4.6 Design for human review

The system supports analysts. It does not silently turn model outputs into final operational decisions.

## 5. High-level logical architecture

```text
                         OFFICIAL DATA SOURCE
                    CFPB Consumer Complaint Database
                                  |
                                  v
                    +-----------------------------+
                    | 1. Ingestion and snapshot   |
                    +-----------------------------+
                                  |
                                  v
                    +-----------------------------+
                    | 2. Validation and audit     |
                    +-----------------------------+
                                  |
                                  v
                    +-----------------------------+
                    | 3. Cleaning and preparation|
                    +-----------------------------+
                                  |
                   +--------------+---------------+
                   |                              |
                   v                              v
       +-------------------------+     +--------------------------+
       | 4A. Classification      |     | 4B. Semantic embeddings  |
       | TF-IDF + Logistic Reg.  |     +--------------------------+
       +-------------------------+                  |
                   |                         +------+------+
                   v                         |             |
       Predictions and evaluation            v             v
                                      Similar-case     Theme
                                      retrieval        clustering
                                                           |
                                                           v
                                               +----------------------+
                                               | 5. Temporal monitor  |
                                               +----------------------+
                                                           |
                                                           v
                                                Emerging-theme alerts
                                                           |
                    +--------------------------------------+-------+
                    |                                              |
                    v                                              v
          +--------------------+                         +------------------+
          | 6A. SQL analytics |                         | 6B. Evidence store|
          +--------------------+                         +------------------+
                    |                                              |
                    v                                              v
          +--------------------+                         +------------------+
          | Power BI dashboard |                         | Future RAG layer |
          +--------------------+                         +------------------+
```

The two branches after cleaning are intentional:

- the supervised branch learns known complaint labels;
- the semantic branch finds related complaints and discovers themes.

They may use the same narratives, but they produce different artifacts and require different evaluation.

## 6. Component responsibilities

| Component | Responsibility | Main input | Main output |
|---|---|---|---|
| Ingestion | Acquire and identify a data snapshot | Official CFPB source | Immutable raw snapshot and metadata |
| Validation | Check schema and data quality | Raw snapshot | Validation report and approved records |
| Preparation | Clean and standardise required fields | Validated records | Processed modelling dataset |
| Classifier | Predict a known product or issue label | Narrative and trained pipeline | Label scores and prediction |
| Evaluator | Measure classifier behaviour | Labels and predictions | Metrics, errors, and calibration results |
| Embedder | Represent narrative meaning numerically | Processed narrative | Dense embedding vector |
| Retriever | Rank related historical complaints | Query and stored embeddings | Similar complaint records |
| Clusterer | Discover groups of related narratives | Embeddings | Theme or cluster assignments |
| Temporal monitor | Measure theme behaviour over time | Theme assignments and dates | Weekly signals and alerts |
| Analytics layer | Prepare consistent reporting tables | Predictions, themes, and alerts | SQL tables or exports |
| Dashboard | Present trends and investigation context | Curated analytical tables | Interactive analyst views |
| RAG layer | Summarise retrieved evidence | Question and retrieved records | Cited, grounded response |

## 7. Data layers

The project separates data according to how much processing it has received.

### 7.1 Raw layer

Purpose: preserve the downloaded snapshot exactly as received.

Examples:

- original complaint CSV;
- snapshot metadata;
- download date;
- source URL;
- file checksum.

Rules:

- do not manually edit raw records;
- do not commit raw complaint data to Git;
- identify the exact snapshot used by an experiment;
- create a new snapshot rather than overwriting an old one when reproducibility matters.

### 7.2 Interim layer

Purpose: store intermediate results that are useful during validation and transformation.

Examples:

- parsed dates;
- standardised column names;
- deduplication candidates;
- label-mapping review tables;
- filtered narrative records.

Interim data is not automatically ready for model training.

### 7.3 Processed layer

Purpose: provide documented, reproducible inputs for modelling and analysis.

Examples:

- complaint identifier;
- validated received date;
- selected narrative text;
- chosen target label;
- split assignment;
- controlled metadata fields.

Processed data must record how it was derived from the raw snapshot.

### 7.4 Artifact layer

Purpose: store outputs produced by trained or fitted components.

Examples:

- fitted TF-IDF vocabulary;
- trained classifier;
- label encoder or label mapping;
- embedding model identifier;
- complaint embeddings or vector index;
- clustering model and assignments;
- anomaly-detection parameters;
- evaluation reports;
- Power BI-ready exports.

Generated artifacts will normally remain outside Git when they are large or reproducible. Their metadata and creation instructions should be versioned.

## 8. Data contracts

A data contract defines the shape and meaning of information passed between components. It reduces silent failures caused by renamed fields, missing values, or changing assumptions.

### 8.1 Processed complaint record

Conceptual fields:

| Field | Meaning |
|---|---|
| `complaint_id` | Stable source record identifier |
| `received_at` | Validated complaint received date |
| `narrative` | Public complaint narrative used as text input |
| `product` | Source product label |
| `issue` | Source issue label |
| `data_split` | Train, validation, or test assignment |
| `snapshot_id` | Identity of the source-data snapshot |

The final field names will be established after inspecting the real dataset.

### 8.2 Classification result

Conceptual fields:

| Field | Meaning |
|---|---|
| `complaint_id` | Record being classified |
| `predicted_label` | Highest-ranked category |
| `prediction_score` | Model confidence or comparable score |
| `alternative_labels` | Other high-ranked categories where supported |
| `model_version` | Exact model artifact used |
| `predicted_at` | Time the prediction was produced |

The score must not be described as a reliable probability until calibration is evaluated.

### 8.3 Similarity result

Conceptual fields:

| Field | Meaning |
|---|---|
| `query_complaint_id` | Complaint used as the search query |
| `matched_complaint_id` | Retrieved historical record |
| `similarity_score` | Vector similarity, not probability |
| `rank` | Position in the result list |
| `embedding_version` | Embedding model used |

### 8.4 Theme assignment

Conceptual fields:

| Field | Meaning |
|---|---|
| `complaint_id` | Complaint assigned to a group |
| `theme_id` | Cluster or topic identifier |
| `assignment_score` | Strength or distance where supported |
| `cluster_version` | Clustering configuration or artifact version |

A human-readable theme label is an interpretation layered on top of the mathematical assignment.

### 8.5 Emerging-risk alert

Conceptual fields:

| Field | Meaning |
|---|---|
| `theme_id` | Monitored complaint theme |
| `period_start` | Beginning of the evaluated period |
| `current_count` | Observed complaint volume |
| `baseline_value` | Historical expected or reference value |
| `anomaly_score` | Output from the selected detection method |
| `alert_reason` | Human-readable trigger explanation |
| `detector_version` | Detection configuration used |
| `review_status` | Pending, reviewed, or dismissed by an analyst |

## 9. Offline learning pipeline

The offline pipeline is used to learn from historical data and evaluate model choices.

```text
Recorded data snapshot
        |
        v
Validate schema and records
        |
        v
Create reproducible processed dataset
        |
        v
Assign train/validation/test data without leakage
        |
        v
Fit text transformation on training data only
        |
        v
Train baseline classifier
        |
        v
Evaluate on unseen data
        |
        v
Save model, configuration, metrics, and error samples
```

Important rule: transformations that learn from data, such as a TF-IDF vocabulary, must be fitted using training data only. Fitting them before the split would allow information from evaluation records to influence the model.

## 10. Batch intelligence pipeline

The first useful version does not require real-time streaming. CFPB data can be processed in batches.

```text
New data snapshot
        |
        v
Validate and prepare new records
        |
        +--------------------------+
        |                          |
        v                          v
Generate predictions       Generate embeddings
                                   |
                                   v
                         Assign or recompute themes
                                   |
                                   v
                         Aggregate weekly volumes
                                   |
                                   v
                         Calculate anomaly signals
                                   |
                                   v
                         Refresh analytical exports
```

Why batch first:

- the public source does not require millisecond response time;
- batch processing is easier to reproduce and debug;
- topic clustering and temporal aggregation naturally operate on groups of records;
- it avoids unnecessary streaming infrastructure during the learning phase.

A future API for single-complaint classification or retrieval can be added after the offline components are reliable.

## 11. Future single-complaint inference flow

This is a later interface, not an implemented service.

```text
New complaint narrative
        |
        v
Input and empty-text validation
        |
        +-------------------------+
        |                         |
        v                         v
Saved TF-IDF pipeline       Saved embedding model
        |                         |
        v                         v
Category suggestion        Similarity search
        |                         |
        +------------+------------+
                     |
                     v
            Human-review response
```

The exact saved preprocessing pipeline must be reused. Reimplementing preprocessing differently at prediction time can create training-serving skew.

## 12. Training path versus inference path

Understanding this distinction is important in interviews.

### Training path

The system learns model parameters from historical labelled complaints. It can inspect true labels, calculate errors, and compare experiments.

### Inference path

The system receives a new narrative without knowing its true label. It loads previously fitted artifacts and produces a suggestion.

### Why the distinction matters

- target labels are available during training but not prediction;
- fitting preprocessing during inference would be incorrect;
- evaluation code should not be part of the prediction response;
- model and transformation versions must remain compatible;
- information available after complaint submission cannot become an inference feature.

## 13. Supervised and unsupervised branches

### Supervised classification

Supervised learning uses examples containing both complaint text and a known source label. The model learns a mapping from text features to those labels.

Question answered:

> Which known category best matches this complaint?

### Unsupervised clustering

Clustering receives complaint representations without using the target label as the answer. It searches for groups based on similarity.

Question answered:

> Which complaints appear to form related groups based on their narratives?

### Why both are needed

Classification creates consistency with an existing taxonomy. Clustering can reveal narrower structures that the taxonomy does not explicitly represent. A cluster is not automatically a new official category; it is a candidate theme requiring interpretation.

## 14. Temporal architecture and leakage boundary

Emerging-risk detection asks what could have been known at a particular point in time. Therefore, the architecture must preserve dates and prevent future information from entering past calculations.

For an alert evaluated at the end of a given week:

- only complaints received by that time may be used;
- the historical baseline must not use later weeks;
- theme construction must be evaluated carefully if it was fitted using the full future dataset;
- future alert outcomes cannot influence threshold selection on the test period.

This is called a temporal or point-in-time correctness boundary.

Company response, resolution, or timely-response information may be useful for retrospective analysis, but those values can occur after complaint arrival. They should not be classifier inputs when the prediction scenario is arrival-time routing.

## 15. Configuration and versioning

Values that can change between experiments should be stored in configuration rather than hidden throughout notebooks.

Examples:

- random seed;
- source snapshot identifier;
- selected target label;
- included classes;
- train and test dates;
- TF-IDF limits;
- classifier parameters;
- embedding model name;
- clustering parameters;
- time aggregation interval;
- anomaly threshold.

A model version alone is not enough. A reproducible experiment links:

```text
Data snapshot + processing version + configuration + code commit
                              |
                              v
                  model and evaluation artifacts
```

## 16. Observability and validation points

Checks should occur at every important boundary.

| Boundary | Example checks |
|---|---|
| Source to raw | Download succeeded, checksum recorded, file readable |
| Raw to interim | Required columns exist, identifiers and dates parse |
| Interim to processed | Narratives present, labels controlled, duplicates handled |
| Processed to training | Split valid, no overlap, class distribution recorded |
| Model to predictions | Artifact compatible, probabilities or scores valid |
| Embeddings to retrieval | Vector dimensions match, identifiers remain aligned |
| Clusters to monitoring | Theme IDs versioned, dates complete, small clusters handled |
| Signals to alerts | Threshold documented, baseline available, evidence linked |
| Analytics to dashboard | Counts reconcile, refresh time visible, definitions consistent |
| Retrieval to RAG | Sources retained, unsupported claims rejected or flagged |

These checks make failures visible instead of allowing incorrect results to flow downstream.

## 17. Failure handling

The system should fail clearly when:

- required columns are missing;
- the source schema changes unexpectedly;
- complaint text is empty or unusable;
- a saved artifact is incompatible with the current configuration;
- an embedding has the wrong dimension;
- dates required for temporal monitoring are invalid;
- a theme lacks enough history to calculate a meaningful baseline;
- no supporting records are retrieved for a requested summary.

It should not silently replace missing data, invent a theme label, or generate an unsupported narrative.

## 18. Security, privacy, and governance boundaries

Even public complaint narratives deserve careful handling.

The architecture should:

- keep raw data outside Git;
- use source-provided public narratives rather than attempting to recover removed details;
- avoid copying unnecessary narrative text into logs;
- restrict future dashboards to appropriate fields;
- preserve source identifiers for traceability;
- record model and data versions;
- keep human review for predictions, alerts, and summaries.

This portfolio project does not yet implement enterprise authentication, access control, encryption infrastructure, or regulatory approval workflows. Those would be required in a real institutional deployment.

## 19. Architecture stages

### Stage 1 — Data and baseline foundation

- acquire and identify the dataset snapshot;
- validate and document the data;
- create a processed modelling dataset;
- train and evaluate the TF-IDF baseline.

### Stage 2 — Semantic intelligence

- create sentence embeddings;
- implement similar-complaint retrieval;
- evaluate retrieved examples;
- discover and interpret complaint themes.

### Stage 3 — Emerging-risk monitoring

- create time-indexed theme counts;
- establish historical baselines;
- compare anomaly-detection methods;
- review alert quality and false-alert behaviour.

### Stage 4 — Analyst communication

- create SQL transformations;
- export documented analytical tables;
- build Power BI views;
- connect alerts to supporting evidence.

### Stage 5 — Grounded language interface

- retrieve evidence for an analytical question;
- generate a source-linked summary;
- evaluate faithfulness and unsupported claims;
- refuse or flag questions without sufficient evidence.

Each stage depends on artifacts from the previous stage. This reduces the chance of adding an impressive-looking interface over unreliable data or models.

## 20. Alternatives considered

### One large notebook

Rejected as the final architecture because it mixes responsibilities, is difficult to test, and makes reproducibility fragile. Notebooks will still be used for exploration and experiment explanation.

### Real-time streaming from the beginning

Deferred because the public-data use case can be served through reproducible batch processing. Streaming would add infrastructure without solving the current learning problem.

### Transformer classifier as the first model

Deferred until the baseline is understood. A transformer may improve contextual understanding but adds computational cost, tuning complexity, and less transparent failure analysis.

### RAG as the central system

Rejected because RAG does not replace classification, clustering, or time-series anomaly detection. It will only provide an interface over retrieved and calculated evidence.

### One model for every task

Rejected because classification, similarity retrieval, clustering, and anomaly detection have different objectives and evaluation methods.

## 21. Architecture risks

| Risk | Why it matters | Planned control |
|---|---|---|
| Source schema changes | Pipelines can silently select wrong data | Explicit schema validation |
| Label drift | Old and new categories may not be comparable | Analyse labels over time and version mappings |
| Data leakage | Evaluation appears better than real use | Fit on training data and enforce time boundaries |
| Training-serving skew | New complaints receive different preprocessing | Save and reuse the full fitted pipeline |
| Unstable clusters | Theme IDs can change between runs | Version settings and measure stability |
| False anomaly alerts | Analysts lose trust or waste time | Minimum volume, historical context, threshold evaluation |
| Artifact mismatch | Predictions become invalid | Store model, preprocessing, and configuration versions |
| RAG hallucination | Summary states unsupported conclusions | Retrieval citations, faithfulness checks, refusal path |

## 22. Current repository mapping

| Repository location | Architectural purpose |
|---|---|
| `configs/` | Versioned experiment settings |
| `data/raw/` | Local immutable downloads, excluded from Git |
| `data/interim/` | Local validation and transformation outputs |
| `data/processed/` | Local modelling-ready datasets |
| `notebooks/` | Exploration and experiment narratives |
| `src/complaint_intelligence/` | Reusable implementation logic |
| `models/` | Generated model artifacts, excluded from Git |
| `sql/` | Reproducible analytical transformations |
| `powerbi/` | Dashboard documentation and future assets |
| `reports/figures/` | Generated visual evidence |
| `tests/` | Behaviour and validation checks |
| `notes/` | Learning decisions and interview defense |

The directories exist, but most pipeline components described in this note are planned rather than implemented.

## 23. Interview-ready explanation

### “Explain the architecture of your project.”

> I designed the system as separate, testable pipelines over a reproducible CFPB data snapshot. Data first passes through schema validation and preparation. One branch uses TF-IDF and Logistic Regression to predict known complaint categories. A second branch creates sentence embeddings for semantic retrieval and theme clustering. Theme assignments are aggregated over time, and anomaly detection flags unusual growth. SQL and Power BI expose the verified outputs, while a later RAG layer only summarises retrieved evidence with citations.

### “Why did you use separate components?”

> The components answer different questions. Classification predicts a known label, retrieval finds related records, clustering discovers groups, and anomaly detection measures unusual temporal behaviour. Separating them allows each task to use the correct inputs, metrics, and failure controls.

### “Why are you starting with batch processing?”

> The public complaint dataset and planned weekly monitoring do not require real-time infrastructure. Batch processing is simpler to reproduce, inspect, and debug. I can add a single-complaint API later without forcing streaming complexity into the initial system.

### “How will you prevent data leakage?”

> I will split data before fitting learned transformations, fit the TF-IDF vocabulary only on training records, exclude post-arrival outcome fields from arrival-time prediction, and ensure temporal alerts use only information available up to the evaluation date.

### “How will you reproduce a result?”

> Every result should be linked to a source snapshot, processing version, experiment configuration, random seed, code commit, and saved artifact metadata. The model file alone is not enough for reproducibility.

### “Where does RAG fit?”

> RAG is the final evidence-explanation layer. It retrieves supporting complaints and calculated results before generating a cited response. It does not replace the classifier, clustering algorithm, or anomaly detector.

## 24. Completion checkpoint

This architecture is a plan, not proof that the system works. Each stage must later be implemented, evaluated, and documented.

Before moving to the technology-stack note, I should be able to explain:

1. why raw, interim, processed, and artifact layers are separate;
2. why classification and clustering are different branches;
3. why temporal monitoring requires point-in-time correctness;
4. why the fitted preprocessing pipeline must be reused at inference;
5. why RAG comes after reliable retrieval;
6. why batch processing is appropriate for the first version.

The core architectural idea is:

> **Every component has one responsibility, an explicit data contract, its own evaluation method, and a traceable path back to the source data.**

