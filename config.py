"""Central configuration: paths and shared constants."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports"
SQL_DIR = ROOT / "sql"
DB_PATH = ROOT / "data" / "learner_analytics.db"
SQL_RESULTS_DIR = REPORTS_DIR / "sql_results"

COURSES = [
    "Data Science",
    "Full Stack Development",
    "DevOps",
    "Data Analytics",
]
N_LEARNERS = 600
N_WEEKS = 12
SEED = 42

# Engagement score weights (must sum to 1.0)
WEIGHTS = {
    "active_weeks_rate": 0.30,
    "assignment_rate": 0.30,
    "live_attendance_rate": 0.20,
    "watch_time_rate": 0.20,
}
WATCH_TARGET_MIN_PER_WEEK = 300   # minutes/week treated as "full" watch-time

# Segmentation thresholds
HIGH_ENGAGEMENT = 70
LOW_ENGAGEMENT = 40
LOW_SCORE_PCT = 50
