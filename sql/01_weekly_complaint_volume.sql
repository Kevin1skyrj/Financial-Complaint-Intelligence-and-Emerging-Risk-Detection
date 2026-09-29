-- Reconcile raw complaint-topic assignments with the monitoring fact table.
-- Expected result: zero differences for every topic-week.

WITH assignment_counts AS (
    SELECT
        date(date_received, '-' || ((strftime('%w', date_received) + 6) % 7) || ' days')
            AS week_start,
        topic_id,
        COUNT(*) AS assignment_count
    FROM fact_complaint_topic
    WHERE date_received BETWEEN '2023-09-04' AND '2024-03-31'
    GROUP BY 1, 2
)
SELECT
    w.week_start,
    w.topic_id,
    COALESCE(a.assignment_count, 0) AS assignment_count,
    w.topic_count AS monitoring_count,
    COALESCE(a.assignment_count, 0) - w.topic_count AS count_difference
FROM fact_weekly_topic_metric AS w
LEFT JOIN assignment_counts AS a
    ON a.week_start = w.week_start
    AND a.topic_id = w.topic_id
ORDER BY w.week_start, w.topic_id;

