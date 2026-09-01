# Architecture decisions

## Separation of tasks

The project separates supervised routing from unsupervised monitoring:

- **Classifier:** predicts an existing product or issue label from complaint text.
- **Retriever:** finds semantically related historical narratives.
- **Topic monitor:** groups related complaints and measures their volume over time.
- **Alert logic:** flags statistically unusual topic growth for analyst review.
- **RAG extension:** summarizes retrieved evidence with citations; it does not replace the classifier.

Keeping these components separate makes their assumptions and evaluation criteria testable.

## First baseline

The first trained model will be TF-IDF with Logistic Regression. It is fast, interpretable, and provides a meaningful benchmark before adding transformer embeddings.

## Leakage boundary

Company responses and other post-submission outcomes must not become classifier inputs when predicting at complaint-arrival time. Temporal experiments will train on older complaints and evaluate on newer complaints.

