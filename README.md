# Learner Engagement and Performance Analytics Dashboard

An end-to-end analytics project that studies how learners engage with an online learning program and how that engagement relates to their performance - to understand participation trends and identify areas that need improvement.

**Tech stack:** Python (Pandas, NumPy) · SQL (SQLite) · Excel (openpyxl, KPI report with charts)

## Objectives
- Clean and transform raw learner, engagement and assessment data
- Build a single **engagement score** per learner and segment learners (High / Medium / Low)
- Use SQL to analyse course performance, weekly participation trends, drop-off and assessment difficulty
- Flag **at-risk learners** so support teams can intervene early
- Deliver KPI-based reports and visual summaries in Excel

## Project structure
```
learner-engagement-analytics/
├── README.md
├── requirements.txt
├── run_pipeline.py                  # runs all steps in order
├── src/
│   ├── config.py                    # paths, weights, thresholds
│   ├── 01_generate_sample_data.py   # creates messy sample raw data
│   ├── 02_clean_transform.py        # Pandas cleaning + feature engineering
│   ├── 03_load_to_sqlite.py         # builds SQLite database
│   ├── 04_run_sql_analysis.py       # runs SQL queries -> CSV results
│   └── 05_build_excel_report.py     # KPI Excel report with charts
├── sql/
│   ├── 01_schema.sql                # tables, keys, indexes
│   └── 02_analysis_queries.sql      # 10 analysis queries (CTEs, window functions)
├── data/
│   ├── raw/                         # raw CSVs
│   └── processed/                   # cleaned CSVs
└── reports/
    ├── learner_engagement_kpi_report.xlsx
    └── sql_results/                 # query outputs
```

## How to run
```bash
pip install -r requirements.txt
python run_pipeline.py
```
Or run each script in `src/` in numeric order. To use real data, place your CSVs in `data/raw/` using the same column names and skip step 01.

> The dataset is **simulated** (600 learners, 4 courses, 12 weeks) because real learner data is private. It includes deliberate quality problems so the cleaning step has real work to do.

## Data cleaning (Pandas)
| Issue | Fix |
|---|---|
| Duplicate learners / weekly rows / assessments | `drop_duplicates` on business keys |
| Inconsistent course names (`DATASCIENCE`, ` devops `) | strip, lower-case, map to official course list |
| Missing city / invalid signup dates | fill `Unknown` / median date |
| Missing sessions, minutes, submissions | impute with weekly median |
| Negative watch minutes | treated as invalid, then imputed |
| Scores above maximum | capped at max score |
| Missing scores | dropped (assessment not attempted) |

## Engagement score (0-100)
`30% active-weeks rate + 30% assignment completion + 20% live-class attendance + 20% watch time`

- **High** >= 70, **Medium** 40-70, **Low** < 40
- **Dropped off:** no activity in the last 3 weeks
- **At risk:** Low engagement, or dropped off, or average score < 50%

## SQL analysis
Queries in `sql/02_analysis_queries.sql`: KPI overview, course performance, weekly engagement trend, week-over-week change (`LAG`), engagement vs performance, assessment difficulty, drop-off timing, city ranking (`RANK`), top learners per course (`ROW_NUMBER`), and at-risk learner list.

## Excel report
- **KPI Dashboard** - total learners, average engagement, average score, assignment completion, drop-off and at-risk rates, plus segment chart
- **Course Summary** - course comparison with chart
- **Weekly Trend** - participation trend with line chart
- **At-Risk** - top 50 learners needing intervention, colour-coded by risk level
- **Learner Data** - cleaned data feeding all formulas

KPIs are live Excel formulas over the data sheet, so the report refreshes when data changes.

## Key findings (on the sample data)
- **Engagement drives performance:** High-engagement learners average ~81% on assessments versus ~54% for Low-engagement learners.
- **DevOps needs attention:** lowest engagement score (41.0), highest drop-off (28.2%) and highest at-risk share (45.6%).
- **Assignments are the weak spot:** only ~43% of assigned work is submitted overall.
- **~40% of learners are at risk**, so early-warning flags have strong potential to support retention.

## Relevance to the education industry
Understanding learner engagement and progress is central to edtech: it helps teams spot struggling learners early, improve course design, and raise completion and outcomes.

## Possible extensions
Predictive drop-off model (logistic regression), cohort retention analysis, Power BI / Tableau dashboard, scheduled refresh.
