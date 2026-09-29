PRAGMA foreign_keys = ON;

CREATE INDEX IF NOT EXISTS idx_complaint_topic_date
    ON fact_complaint_topic(date_received);
CREATE INDEX IF NOT EXISTS idx_complaint_topic_topic
    ON fact_complaint_topic(topic_id);
CREATE INDEX IF NOT EXISTS idx_complaint_topic_product
    ON fact_complaint_topic(product);
CREATE INDEX IF NOT EXISTS idx_weekly_topic_week
    ON fact_weekly_topic_metric(week_start);
CREATE INDEX IF NOT EXISTS idx_weekly_topic_topic
    ON fact_weekly_topic_metric(topic_id);
CREATE INDEX IF NOT EXISTS idx_risk_alert_week
    ON fact_risk_alert(week_start);

DROP VIEW IF EXISTS vw_complaint_detail;
CREATE VIEW vw_complaint_detail AS
SELECT
    complaint_id,
    date_received,
    date(date_received, '-' || ((strftime('%w', date_received) + 6) % 7) || ' days') AS week_start,
    product,
    issue,
    company,
    state,
    submitted_via,
    topic_id
FROM fact_complaint_topic;

DROP VIEW IF EXISTS vw_topic_catalog;
CREATE VIEW vw_topic_catalog AS
SELECT
    topic_id,
    top_terms,
    historical_rows,
    dominant_product,
    dominant_product_share,
    product_count
FROM dim_topic;

DROP VIEW IF EXISTS vw_weekly_topic_dashboard;
CREATE VIEW vw_weekly_topic_dashboard AS
SELECT
    w.week_start,
    w.topic_id,
    t.top_terms,
    t.dominant_product,
    w.topic_count,
    w.total_complaints,
    w.topic_share,
    w.baseline_share_median,
    w.share_increase,
    w.robust_z_score,
    w.candidate_signal,
    w.persistent_signal_count,
    w.alert,
    w.severity
FROM fact_weekly_topic_metric AS w
JOIN dim_topic AS t USING (topic_id);

DROP VIEW IF EXISTS vw_alert_dashboard;
CREATE VIEW vw_alert_dashboard AS
SELECT
    a.week_start,
    a.topic_id,
    t.top_terms,
    t.dominant_product,
    a.topic_count,
    a.total_complaints,
    a.topic_share,
    a.baseline_share_median,
    a.share_increase,
    a.robust_z_score,
    a.persistent_signal_count,
    a.severity
FROM fact_risk_alert AS a
JOIN dim_topic AS t USING (topic_id);

DROP VIEW IF EXISTS vw_product_topic_summary;
CREATE VIEW vw_product_topic_summary AS
SELECT
    product,
    topic_id,
    COUNT(*) AS complaint_count,
    ROUND(
        CAST(COUNT(*) AS REAL)
        / SUM(COUNT(*)) OVER (PARTITION BY product),
        6
    ) AS share_within_product
FROM fact_complaint_topic
GROUP BY product, topic_id;

DROP VIEW IF EXISTS vw_weekly_overview;
CREATE VIEW vw_weekly_overview AS
SELECT
    week_start,
    MAX(total_complaints) AS narrative_complaints,
    SUM(CASE WHEN alert = 1 THEN 1 ELSE 0 END) AS alert_count,
    SUM(CASE WHEN candidate_signal = 1 THEN 1 ELSE 0 END) AS candidate_count,
    COUNT(DISTINCT topic_id) AS monitored_topics,
    MAX(robust_z_score) AS maximum_robust_z_score
FROM fact_weekly_topic_metric
GROUP BY week_start;

DROP VIEW IF EXISTS vw_model_summary;
CREATE VIEW vw_model_summary AS
SELECT
    model_name,
    accuracy,
    balanced_accuracy,
    macro_f1,
    weighted_f1,
    majority_accuracy,
    majority_macro_f1,
    expected_calibration_error,
    multiclass_log_loss,
    multiclass_brier_score,
    evaluation_scope
FROM fact_model_summary;

DROP VIEW IF EXISTS vw_model_class_performance;
CREATE VIEW vw_model_class_performance AS
SELECT
    product,
    precision,
    recall,
    f1_score,
    support
FROM fact_model_class_metric;
