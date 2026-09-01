-- Planned analytical query for the emerging-risk milestone.
-- Column names will be adapted to the validated processed-data schema.

SELECT
    DATE_TRUNC('week', received_at) AS complaint_week,
    topic_id,
    COUNT(*) AS complaint_count
FROM complaint_topics
GROUP BY 1, 2
ORDER BY 1, 2;

