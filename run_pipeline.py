"""Run the full pipeline: generate data -> clean -> load SQL -> analyse -> Excel report."""
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).parent / "src"
STEPS = [
    "01_generate_sample_data.py",   # skip this step if you use your own raw CSVs
    "02_clean_transform.py",
    "03_load_to_sqlite.py",
    "04_run_sql_analysis.py",
    "05_build_excel_report.py",
]

for step in STEPS:
    print(f"\n>>> Running {step}")
    subprocess.run([sys.executable, str(SRC / step)], check=True, cwd=SRC)
print("\nPipeline complete. Open reports/learner_engagement_kpi_report.xlsx")
