"""Step 3 - Create the SQLite database and load the cleaned CSVs."""
import sqlite3
import pandas as pd
from config import DB_PATH, PROCESSED_DIR, SQL_DIR

TABLES = {
    "learners": "learners_clean.csv",
    "engagement": "engagement_clean.csv",
    "assessments": "assessments_clean.csv",
    "learner_summary": "learner_summary.csv",
}


def main():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript((SQL_DIR / "01_schema.sql").read_text())
        for table, csv in TABLES.items():
            df = pd.read_csv(PROCESSED_DIR / csv)
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
            df[cols].to_sql(table, conn, if_exists="append", index=False)
            print(f"Loaded {len(df):>6} rows into {table}")
    print(f"Database ready: {DB_PATH}")


if __name__ == "__main__":
    main()
