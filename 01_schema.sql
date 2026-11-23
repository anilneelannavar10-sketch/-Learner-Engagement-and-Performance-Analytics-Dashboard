-- Schema for the Learner Engagement & Performance database (SQLite)

DROP TABLE IF EXISTS learners;
DROP TABLE IF EXISTS engagement;
DROP TABLE IF EXISTS assessments;
DROP TABLE IF EXISTS learner_summary;

CREATE TABLE learners (
    learner_id  TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    city        TEXT,
    course      TEXT NOT NULL,
    signup_date DATE
);

CREATE TABLE engagement (
    learner_id             TEXT NOT NULL REFERENCES learners(learner_id),
    week                   INTEGER NOT NULL,
    sessions               INTEGER,
    minutes_watched        INTEGER,
    assignments_due        INTEGER,
    assignments_submitted  INTEGER,
    live_classes_scheduled INTEGER,
    live_classes_attended  INTEGER,
    forum_posts            INTEGER,
    is_active              INTEGER,
    PRIMARY KEY (learner_id, week)
);

CREATE TABLE assessments (
    learner_id TEXT NOT NULL REFERENCES learners(learner_id),
    assessment TEXT NOT NULL,
    score      REAL,
    max_score  REAL,
    score_pct  REAL,
    PRIMARY KEY (learner_id, assessment)
);

-- Learner-level table produced by the Pandas pipeline
CREATE TABLE learner_summary (
    learner_id TEXT PRIMARY KEY,
    name TEXT, city TEXT, course TEXT, signup_date DATE,
    total_sessions REAL, total_minutes REAL, weeks_tracked INTEGER, active_weeks INTEGER,
    assignments_due INTEGER, assignments_submitted INTEGER,
    live_scheduled INTEGER, live_attended INTEGER, forum_posts INTEGER,
    active_weeks_rate REAL, assignment_rate REAL, live_attendance_rate REAL,
    avg_weekly_minutes REAL, watch_time_rate REAL, engagement_score REAL,
    last_active_week INTEGER, avg_score_pct REAL, assessments_taken INTEGER,
    engagement_segment TEXT, dropped_off INTEGER, at_risk INTEGER
);

CREATE INDEX idx_eng_week ON engagement(week);
CREATE INDEX idx_learners_course ON learners(course);
