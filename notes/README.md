# Project Learning and Interview Notes

This folder documents the project in the same order in which it is learned and built. The notes are intended to serve two purposes:

1. explain every important data-science concept in beginner-friendly language;
2. record enough reasoning, evidence, and limitations to defend the project honestly in an interview.

## How to use these notes

Read the files in numerical order. A note should be updated when the related milestone is implemented, tested, or changed. Planned work must remain clearly separated from completed work.

Each technical note will answer:

- What does this concept mean?
- Why does this project need it?
- How does it work at a high level?
- Why was this approach chosen?
- What alternatives and trade-offs exist?
- What was actually implemented and verified?
- What could go wrong?
- How can the decision be explained in an interview?

## Note index

| No. | File | Purpose | Status |
|---|---|---|---|
| 00 | [`00_project_overview.md`](00_project_overview.md) | What the project is, why it exists, how it helps, and its boundaries | Complete |
| 01 | [`01_problem_and_use_cases.md`](01_problem_and_use_cases.md) | Stakeholders, use cases, requirements, and success criteria | Complete |
| 02 | [`02_system_architecture.md`](02_system_architecture.md) | Components, data flow, inputs, outputs, and design decisions | Complete |
| 03 | [`03_technology_stack.md`](03_technology_stack.md) | Every technology, why it is used, and possible alternatives | Complete |
| 04 | [`04_dataset_understanding.md`](04_dataset_understanding.md) | CFPB source, fields, target labels, limitations, and data dictionary | Draft complete; review required |
| 04A | [`04a_dataset_acquisition_plan.md`](04a_dataset_acquisition_plan.md) | Archive selection, provenance, storage, verification, and download procedure | Acquisition and extraction completed |
| 04B | [`04b_schema_inspection.md`](04b_schema_inspection.md) | Safe extraction, archived schema, row coverage, and first quality results | Implemented; results verified |
| 05 | [`05_data_cleaning_and_eda.md`](05_data_cleaning_and_eda.md) | Data-quality checks, cleaning decisions, and exploratory analysis | Implemented; results verified |
| 06 | [`06_text_preprocessing.md`](06_text_preprocessing.md) | Conservative text handling and leakage-safe chronological splits | Implemented; results verified |
| 07 | [`07_baseline_model.md`](07_baseline_model.md) | TF-IDF, Logistic Regression, training flow, and model assumptions | Implemented; results verified |
| 08 | [`08_model_evaluation.md`](08_model_evaluation.md) | Metrics, imbalance, validation, error analysis, and calibration | Implemented; results verified |
| 09 | [`09_semantic_search.md`](09_semantic_search.md) | Searchable TF-IDF similarity baseline, retrieval metrics, and semantic-upgrade boundary | Baseline implemented; neural embeddings remain planned |
| 10 | `10_topic_clustering.md` | Theme discovery, clustering choices, and cluster evaluation | Planned |
| 11 | `11_emerging_risk_detection.md` | Weekly topic signals, anomaly detection, and alert interpretation | Planned |
| 12 | `12_sql_and_powerbi.md` | Analytical tables, queries, dashboard design, and business views | Planned |
| 13 | `13_rag_extension.md` | Evidence-grounded summaries, retrieval flow, and hallucination controls | Planned |
| 14 | `14_limitations_and_responsible_ai.md` | Bias, privacy, misuse risks, monitoring, and human oversight | Planned |
| 15 | `15_interview_questions.md` | Project explanation and technical follow-up questions | Planned |

## Documentation rules

- Do not record a planned feature as completed.
- Do not publish model metrics without a reproducible experiment.
- Record why a decision was made, not only what was done.
- Include failed experiments and what they taught us when relevant.
- Keep dataset limitations and leakage risks visible.
- Prefer clear explanations over memorised definitions.
- Update the README and resume only after verified milestones.
