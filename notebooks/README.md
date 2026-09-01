# Notebook sequence

Notebooks will be added only as each milestone is implemented:

1. `01_data_audit.ipynb` — source, schema, missingness, duplicates, labels, and time coverage.
2. `02_text_eda.ipynb` — narrative length, label imbalance, vocabulary, and sampling bias.
3. `03_baseline_classifier.ipynb` — TF-IDF baseline and class-level error analysis.
4. `04_embeddings_and_clusters.ipynb` — semantic retrieval and topic discovery.
5. `05_emerging_risk.ipynb` — temporal aggregation and anomaly detection.

Reusable logic should move into `src/`; notebooks should document experiments rather than become the production codebase.

