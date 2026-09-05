# 01 — Problem Definition and Use Cases

## 1. Purpose of this note

Before choosing a model or writing code, we must define the problem precisely. A technically impressive model is not useful if it solves the wrong problem, uses unavailable information, or produces an output that nobody can act on.

This note defines:

- the problem the project will solve;
- the intended users and their needs;
- the main and supporting use cases;
- the inputs and outputs for each use case;
- functional and non-functional requirements;
- success criteria and failure conditions;
- assumptions, limitations, and project boundaries.

The definitions in this document are the current design. They may be refined after the dataset is inspected, but any change must be documented rather than made silently.

## 2. Problem statement

Financial complaint records contain useful signals about customer difficulties, but much of that information is stored in unstructured narratives. Reading, categorising, comparing, and monitoring a large complaint collection manually is slow and inconsistent.

The core problem is:

> How can we convert public financial complaint narratives into structured, searchable, and time-aware intelligence that helps a human analyst classify new complaints, find related historical cases, and notice rapidly growing complaint themes?

This is not one machine-learning task. It is a connected system containing supervised learning, information retrieval, unsupervised learning, temporal analysis, and reporting.

## 3. Why the problem is difficult

### 3.1 Complaints are written in natural language

People can describe the same issue using different words, spelling, detail, and emotion.

```text
“The lender charged my monthly instalment twice.”
“There are two EMI debits for the same month.”
“My loan payment was duplicated.”
```

These narratives may describe the same issue even though they share few exact words.

### 3.2 Categories are imbalanced

Some financial products and issues may have many complaint examples, while others may have relatively few. A model can achieve high overall accuracy by performing well on common classes and poorly on rare ones.

This is why class-level precision, recall, and macro F1 will matter more than accuracy alone.

### 3.3 Official labels may be broad or change over time

An existing issue category can contain several narrower customer problems. Labels and products may also be renamed, merged, or introduced during the dataset's history.

Classification can organise complaints according to known labels, while clustering can help discover narrower themes. The two tasks are related but not interchangeable.

### 3.4 Complaint behaviour changes over time

Language, products, customer behaviour, reporting volume, and issue frequency can change. A model trained only on older data may perform differently on newer complaints.

Temporal order must therefore be respected during monitoring experiments and possibly during model validation.

### 3.5 An unusual pattern is not proof of wrongdoing

A sudden increase in complaints can have several explanations, such as a genuine operational issue, increased product usage, reporting campaigns, seasonal effects, changes in data collection, or random variation.

The project will create investigation signals, not legal or factual conclusions.

## 4. Intended users

The project is a portfolio prototype built with public data. The following personas describe plausible users whose needs guide the design; they do not imply deployment inside a real company.

### 4.1 Complaint operations analyst

This analyst reads incoming complaints and decides how they should be categorised or routed.

Needs:

- a suggested product or issue category;
- a confidence score rather than an unexplained label;
- similar historical cases for context;
- the ability to review the original narrative;
- a clear indication when the model is uncertain.

### 4.2 Risk or compliance analyst

This analyst investigates patterns that may indicate operational, conduct, or customer-experience risk.

Needs:

- themes whose volume is increasing unusually;
- historical volume for comparison;
- supporting complaints behind each alert;
- filters by time, product, issue, company, or region where appropriate;
- an explanation of why the pattern was flagged.

### 4.3 Product or service manager

This user wants to understand recurring customer pain points and changes in product experience.

Needs:

- trend summaries;
- frequent and emerging themes;
- representative complaints;
- breakdowns by product and period;
- information that can support prioritisation without overstating certainty.

### 4.4 Data scientist or model-risk reviewer

This reviewer evaluates whether the system is reliable, reproducible, and appropriately limited.

Needs:

- dataset and experiment versions;
- class-level evaluation;
- error analysis and calibration;
- leakage controls;
- evidence of drift or changing labels;
- documented assumptions and known limitations.

## 5. Primary use cases

### Use case 1 — Suggest a category for a new complaint

### User goal

Help a complaint analyst determine the likely product or issue associated with a narrative.

### Input

- a complaint narrative;
- only information that would be available when the complaint is received.

### Processing

1. Validate that usable text is present.
2. Apply the same text preparation used during training.
3. Transform the narrative into model features.
4. Generate class probabilities or decision scores.
5. Return the most likely category and alternatives.

### Planned output

```text
Suggested product: Credit card
Confidence: 0.78
Alternative category: Credit reporting — 0.14
Review status: Human confirmation required
```

### Value

The suggestion can make initial categorisation faster and more consistent.

### Main risks

- the correct category may be rare;
- one narrative may mention multiple products or issues;
- low confidence may be hidden if only the top label is displayed;
- a prediction can appear authoritative even when it is wrong.

### Required safeguard

The result must be presented as a suggestion. Low-confidence or ambiguous complaints must be reviewable rather than forced into an automatic decision.

### Use case 2 — Retrieve similar historical complaints

### User goal

Find complaints that express the same underlying problem even when they use different wording.

### Input

- a new or selected complaint narrative;
- optional filters such as product or time range.

### Processing

1. Convert the query narrative into a sentence embedding.
2. Compare it with embeddings for historical complaints.
3. Rank records by semantic similarity.
4. Apply metadata filters if requested.

### Planned output

- ranked complaint identifiers;
- similarity scores;
- short narrative excerpts;
- relevant metadata;
- links or references to the source records.

### Value

An analyst can see whether similar cases exist and can collect context for investigation.

### Main risks

- high vector similarity does not guarantee the same business issue;
- repeated or near-duplicate records can dominate results;
- private or sensitive text must not be exposed improperly;
- similarity scores can be misread as probabilities.

### Required safeguard

Retrieval quality must be evaluated separately from classification, and the interface must label similarity as similarity—not certainty or risk.

### Use case 3 — Discover complaint themes

### User goal

Find narrower patterns that may be hidden inside broad official categories.

### Input

- complaint embeddings;
- selected time period and optional product filters.

### Processing

1. Group semantically related complaint embeddings.
2. Examine representative complaints from each group.
3. Derive a human-readable description only after reviewing evidence.
4. measure cluster size, coherence, and stability.

### Planned output

```text
Theme identifier: T-017
Analyst label: Duplicate instalment deductions
Complaint count: 126
Representative complaint references: [...]
```

### Value

The discovered themes can reveal specific customer problems that are obscured by broader labels.

### Main risks

- a mathematical cluster may not represent a meaningful business theme;
- the number of clusters can change the interpretation;
- small clusters may be noise;
- an automatically generated label may misrepresent the underlying records.

### Required safeguard

Cluster names must be treated as analyst-reviewed descriptions. Coherence and stability must be inspected before using clusters for monitoring.

### Use case 4 — Detect an emerging complaint theme

### User goal

Identify themes whose recent complaint volume is unusual compared with their historical behaviour.

### Input

- complaint theme assignments;
- complaint received dates;
- weekly or another justified time aggregation.

### Processing

1. Count complaints for every theme and time period.
2. Establish a historical baseline.
3. compare the latest value with expected variation.
4. apply minimum-volume and alert rules.
5. rank alerts for human review.

### Planned output

```text
Theme: Duplicate instalment deductions
Current weekly count: 57
Historical weekly baseline: 8–13
Signal: Unusual increase
Action: Analyst review required
```

### Value

Risk or operations teams may notice a growing customer problem earlier than they would through manual monthly summaries.

### Main risks

- seasonality can create false alerts;
- data-source changes can look like genuine increases;
- low-volume topics can produce unstable growth percentages;
- one complaint may be assigned to the wrong theme;
- repeated alerts can create analyst fatigue.

### Required safeguard

Every alert must show its historical context and supporting complaints. Alert thresholds must balance missed signals against false-alert workload.

## 6. Supporting use cases

### Use case 5 — Monitor model quality

Track class-level performance, confidence, vocabulary changes, label distribution, and errors over time. This helps determine when the model may need investigation or retraining.

### Use case 6 — Explore complaint trends in Power BI

Allow analysts to filter complaint volume, category mix, themes, and alerts by relevant dimensions using curated SQL outputs.

### Use case 7 — Generate a grounded analytical summary

Retrieve complaint evidence and calculated results before asking a language model to create a summary with citations. This is a later extension, not part of the first machine-learning baseline.

## 7. Use-case priorities

The system should not attempt every feature at once.

| Priority | Use case | Reason |
|---|---|---|
| P0 | Data validation and understanding | Every later result depends on knowing the data correctly |
| P1 | Complaint classification baseline | Establishes a measurable and interpretable NLP benchmark |
| P1 | Model evaluation and error analysis | Determines whether the classifier is actually useful |
| P2 | Similar-complaint retrieval | Adds semantic investigation capability |
| P2 | Complaint-theme discovery | Creates the units required for theme monitoring |
| P2 | Emerging-risk detection | Provides the main differentiating business capability |
| P3 | SQL and Power BI reporting | Communicates verified outputs to analysts |
| P3 | Grounded RAG summaries | Added only after reliable retrieval and evidence exist |

`P0` must be completed before `P1`, and the relevant `P2` components must exist before emerging-theme alerts can be trusted.

## 8. Functional requirements

Functional requirements describe what the system should do.

### Data requirements

- Load a versioned or reproducibly identified CFPB data snapshot.
- Validate required columns and data types.
- Detect missing narratives, duplicate identifiers, invalid dates, and label changes.
- Preserve a clear boundary between raw, interim, and processed data.
- Exclude raw complaint data from Git.

### Classification requirements

- Train a reproducible baseline from complaint narratives.
- Return a predicted category and a confidence or score.
- report class-level evaluation, not only overall accuracy.
- Retain examples needed for error analysis.
- Avoid features that would be unavailable at complaint-arrival time.

### Retrieval and clustering requirements

- Generate and version complaint embeddings.
- Retrieve a configurable number of similar complaints.
- Keep complaint identifiers and metadata linked to embeddings.
- Produce cluster assignments and representative records.
- Make cluster interpretation reviewable by a human.

### Monitoring requirements

- Aggregate theme volume over a defined time interval.
- Compare recent values with a historical baseline.
- Apply documented alert rules.
- Retain supporting records and the reason for each alert.
- Allow thresholds to be evaluated and adjusted.

### Reporting requirements

- Produce documented SQL or tabular outputs.
- Show complaint trends, model quality, and alert context.
- Clearly separate observed facts, model predictions, and generated text.

## 9. Non-functional requirements

Non-functional requirements describe how the system should behave.

### Reproducibility

A result should be traceable to the dataset snapshot, configuration, code version, random seed, and evaluation procedure that produced it.

### Interpretability

The baseline model and alert logic should be understandable enough to inspect. A more complex model should only replace a simpler one when it provides a meaningful and verified improvement.

### Privacy and responsible handling

Only appropriately published complaint narratives will be used. Raw narratives will not be committed to Git, and generated outputs must not reintroduce personal information.

### Reliability

Missing input, schema changes, empty text, unseen labels, and unavailable artifacts should produce clear failures rather than silent incorrect results.

### Maintainability

Reusable logic should live in the Python package, configurations should be versioned, and notebooks should document experiments rather than contain all project logic.

### Human oversight

Predictions, cluster descriptions, alerts, and generated summaries must remain reviewable. The system should make uncertainty visible.

## 10. Success criteria

Success must be defined separately for each component.

### Data milestone succeeds when

- the source and snapshot are recorded;
- fields and row meaning are understood;
- missingness, duplicates, labels, dates, and selection limitations are documented;
- leakage risks are identified before modelling.

### Classification milestone succeeds when

- a reproducible baseline is trained;
- metrics are reported on unseen data;
- rare-category performance and errors are analysed;
- results are compared with simple reference strategies;
- limitations are documented honestly.

The exact acceptable metric thresholds will be chosen only after target classes and baseline difficulty are understood. Choosing a target number now would be arbitrary.

### Retrieval milestone succeeds when

- retrieved records are meaningfully related to the query in a reviewed sample;
- metadata filters work correctly;
- duplicates and irrelevant matches are analysed;
- retrieval quality is evaluated using a documented procedure.

### Theme-discovery milestone succeeds when

- clusters are coherent enough for a human to interpret;
- representative examples support the theme description;
- unstable or noisy clusters are identified;
- cluster decisions are reproducible from recorded settings.

### Emerging-risk milestone succeeds when

- alerts are based only on information available up to the evaluated time;
- historical baselines and alert reasons are visible;
- false-alert behaviour is measured;
- alerts link back to supporting complaints;
- the method is compared with a simple volume-growth baseline.

### Communication milestone succeeds when

- the dashboard distinguishes facts, predictions, and alerts;
- every displayed metric has a clear definition;
- a reviewer can trace a chart or summary back to its source data;
- documentation matches the implemented state.

## 11. Failure conditions

The project should be considered misleading or unsuccessful if:

- it reports accuracy without examining class imbalance;
- future or post-outcome information leaks into model inputs;
- random splitting creates unrealistic temporal evaluation;
- a cluster is automatically treated as a real business issue without review;
- an anomaly is described as proof of misconduct;
- generated summaries lack supporting records;
- metrics cannot be reproduced;
- planned functionality is presented as already built;
- complaint counts are interpreted as population-wide issue prevalence;
- the project becomes a collection of disconnected technologies without a coherent user need.

## 12. Important design decisions

### Decision 1 — Build decision support, not automated decision-making

Reason: complaint categories, themes, and anomalies can be ambiguous. Human review reduces the risk of treating a model output as unquestionable truth.

### Decision 2 — Start with an interpretable baseline

Reason: TF-IDF with Logistic Regression is easier to inspect, faster to train, and provides a meaningful benchmark. Advanced NLP is only valuable if it solves an observed baseline limitation.

### Decision 3 — Keep classification and clustering separate

Reason: classification predicts known labels, while clustering searches for structure without those labels. Combining them conceptually would make evaluation unclear.

### Decision 4 — Keep anomaly detection separate from classification

Reason: the classifier asks “what type of complaint is this?” Anomaly detection asks “is the volume or behaviour of this theme unusual over time?” They use different inputs and require different validation.

### Decision 5 — Add RAG last

Reason: a grounded summary requires reliable retrieval and traceable evidence. Adding a language model before building those foundations would create a demonstration without trustworthy support.

## 13. Assumptions that must be tested

- Enough complaints contain usable public narratives.
- Product or issue labels are sufficiently consistent for a baseline target.
- Narrative text contains useful information for the chosen label.
- Dates are complete enough for temporal analysis.
- Embedding similarity can retrieve business-relevant cases.
- Discovered themes are stable enough to monitor over time.
- Historical complaint volume provides a meaningful baseline after accounting for data changes.
- A useful dashboard can be built without exposing sensitive narrative content.

These are hypotheses, not confirmed facts. Dataset analysis and experiments will test them.

## 14. Example user story

> As a risk analyst, I want to see complaint themes with unusual weekly growth so that I can review supporting complaints and decide whether the pattern requires operational investigation.

Acceptance criteria for this story:

1. The alert names or identifies the theme.
2. It shows current and historical complaint volume.
3. It explains the rule or score that triggered the alert.
4. It provides representative supporting complaint references.
5. It indicates uncertainty and requires human review.
6. It can be reproduced from the same data snapshot and configuration.

## 15. Interview-ready explanation

### “What problem does your project solve?”

> Financial complaints contain valuable signals, but their narratives are unstructured and difficult to analyse at scale. My project is designed to classify complaint text, retrieve semantically similar historical cases, discover narrower complaint themes, and monitor those themes over time for unusual growth. The outputs support human investigation rather than making automated lending or compliance decisions.

### “Who is the user of your system?”

> I designed the prototype around complaint operations analysts, risk analysts, product teams, and model reviewers. Operations users need category suggestions and similar cases, risk teams need evidence-backed emerging-theme alerts, and model reviewers need reproducible class-level evaluation and documented limitations.

### “Why is it not just a text-classification project?”

> Classification only maps a complaint to an existing label. It cannot discover a new theme inside a broad category or determine whether that theme is growing unusually over time. Semantic retrieval, clustering, and temporal anomaly detection solve those separate parts of the business problem.

### “How will you measure whether it is useful?”

> Each component needs its own evaluation. Classification will use class-level metrics and error analysis, retrieval will use relevance assessment, clustering will use coherence and stability checks, and emerging-risk detection will measure false alerts and time-based detection behaviour. I will not use one accuracy number to represent the entire system.

### “What is the biggest misuse risk?”

> The biggest risk is treating a prediction or unusual complaint spike as proof. The system only produces suggestions and investigation signals. Outputs must show uncertainty, historical context, and supporting records, with a human responsible for the final interpretation.

## 16. Questions to revisit after data understanding

1. Which label should be the first classification target: product, issue, or a controlled subset?
2. What is the minimum narrative and class quality required for modelling?
3. Should validation be random, time-based, or both for the first classifier?
4. How have CFPB categories and reporting volumes changed over time?
5. Which metadata filters improve retrieval without introducing leakage?
6. What level of cluster stability is sufficient for temporal monitoring?
7. Which alert definition balances early detection and analyst workload?
8. What information can safely appear in the dashboard?

## 17. Completion checkpoint

This milestone defines the intended problem and use cases. It does not prove that every planned capability is feasible. Feasibility will be tested progressively through data inspection and controlled experiments.

Before moving forward, I should be able to explain:

> The classifier organises known complaint types, semantic retrieval finds related cases, clustering discovers narrower themes, and anomaly detection monitors whether those themes are changing unusually over time. Each component supports a specific human user and requires its own evaluation.
