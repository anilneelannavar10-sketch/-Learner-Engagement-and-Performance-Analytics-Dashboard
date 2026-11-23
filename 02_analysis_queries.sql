-- Analysis queries. Each block starts with "-- name: <query_name>"
-- and is executed by src/04_run_sql_analysis.py (results saved as CSV).

-- name: kpi_overview
SELECT
    COUNT(*)                                        AS total_learners,
    ROUND(AVG(engagement_score), 1)                 AS avg_engagement_score,
    ROUND(AVG(avg_score_pct), 1)                    AS avg_score_pct,
    ROUND(100.0 * SUM(dropped_off) / COUNT(*), 1)   AS dropoff_rate_pct,
    ROUND(100.0 * SUM(at_risk) / COUNT(*), 1)       AS at_risk_pct,
    ROUND(100.0 * SUM(assignments_submitted) / SUM(assignments_due), 1) AS assignment_completion_pct
FROM learner_summary;

-- name: course_performance
SELECT
    course,
    COUNT(*)                                       AS learners,
    ROUND(AVG(engagement_score), 1)                AS avg_engagement,
    ROUND(AVG(avg_score_pct), 1)                   AS avg_score_pct,
    ROUND(100.0 * SUM(dropped_off) / COUNT(*), 1)  AS dropoff_rate_pct,
    ROUND(100.0 * SUM(at_risk) / COUNT(*), 1)      AS at_risk_pct
FROM learner_summary
GROUP BY course
ORDER BY avg_engagement DESC;

-- name: weekly_engagement_trend
SELECT
    week,
    SUM(is_active)                                         AS active_learners,
    ROUND(100.0 * SUM(is_active) / COUNT(*), 1)            AS active_rate_pct,
    ROUND(AVG(minutes_watched), 1)                         AS avg_minutes,
    ROUND(100.0 * SUM(assignments_submitted)
                / SUM(assignments_due), 1)                 AS assignment_rate_pct,
    ROUND(100.0 * SUM(live_classes_attended)
                / SUM(live_classes_scheduled), 1)          AS live_attendance_pct
FROM engagement
GROUP BY week
ORDER BY week;

-- name: week_over_week_change
WITH weekly AS (
    SELECT week, SUM(is_active) AS active_learners
    FROM engagement GROUP BY week
)
SELECT
    week,
    active_learners,
    LAG(active_learners) OVER (ORDER BY week)                              AS prev_week,
    ROUND(100.0 * (active_learners - LAG(active_learners) OVER (ORDER BY week))
          / LAG(active_learners) OVER (ORDER BY week), 1)                  AS wow_change_pct
FROM weekly;

-- name: engagement_vs_performance
SELECT
    engagement_segment,
    COUNT(*)                             AS learners,
    ROUND(AVG(avg_score_pct), 1)         AS avg_score_pct,
    ROUND(AVG(assignment_rate) * 100, 1) AS avg_assignment_rate_pct
FROM learner_summary
GROUP BY engagement_segment
ORDER BY CASE engagement_segment WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END;

-- name: assessment_difficulty
SELECT
    assessment,
    COUNT(*)                     AS attempts,
    ROUND(AVG(score_pct), 1)     AS avg_score_pct,
    ROUND(100.0 * SUM(CASE WHEN score_pct < 50 THEN 1 ELSE 0 END) / COUNT(*), 1) AS fail_rate_pct
FROM assessments
GROUP BY assessment
ORDER BY avg_score_pct;

-- name: dropoff_by_last_active_week
SELECT
    last_active_week,
    COUNT(*) AS learners
FROM learner_summary
WHERE dropped_off = 1
GROUP BY last_active_week
ORDER BY last_active_week;

-- name: city_engagement_ranking
SELECT
    city,
    COUNT(*)                        AS learners,
    ROUND(AVG(engagement_score), 1) AS avg_engagement,
    RANK() OVER (ORDER BY AVG(engagement_score) DESC) AS engagement_rank
FROM learner_summary
WHERE city <> 'Unknown'          -- exclude learners with missing city
GROUP BY city
HAVING COUNT(*) >= 10;

-- name: top_learners_per_course
SELECT course, name, learner_id, engagement_score, avg_score_pct, course_rank
FROM (
    SELECT course, name, learner_id, engagement_score, avg_score_pct,
           ROW_NUMBER() OVER (PARTITION BY course ORDER BY engagement_score DESC) AS course_rank
    FROM learner_summary
)
WHERE course_rank <= 5
ORDER BY course, course_rank;

-- name: at_risk_learners
SELECT
    learner_id, name, course, city,
    engagement_score, avg_score_pct, last_active_week,
    CASE
        WHEN dropped_off = 1 AND engagement_score < 40 THEN 'Critical'
        WHEN dropped_off = 1 OR engagement_score < 40  THEN 'High'
        ELSE 'Moderate'
    END AS risk_level
FROM learner_summary
WHERE at_risk = 1
ORDER BY engagement_score ASC
LIMIT 50;
