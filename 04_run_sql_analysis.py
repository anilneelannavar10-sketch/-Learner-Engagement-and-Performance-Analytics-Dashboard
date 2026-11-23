"""Step 4 - Run every query in sql/02_analysis_queries.sql and save results as CSV."""
import re
import sqlite3
import pandas as pd
from config import DB_PATH, SQL_DIR, SQL_RESULTS_DIR


def parse_queries(text):
    blocks = re.split(r"^-- name:\s*(\w+)\s*$", text, flags=re.MULTILINE)
    return dict(zip(blocks[1::2], [b.strip() for b in blocks[2::2]]))


def main():
    SQL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    queries = parse_queries((SQL_DIR / "02_analysis_queries.sql").read_text())
    with sqlite3.connect(DB_PATH) as conn:
        for name, sql in queries.items():
            df = pd.read_sql_query(sql, conn)
            df.to_csv(SQL_RESULTS_DIR / f"{name}.csv", index=False)
            print(f"\n=== {name} ({len(df)} rows) ===")
            print(df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
