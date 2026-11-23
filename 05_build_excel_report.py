"""
Step 5 - Build the KPI-based Excel report with openpyxl.

Sheets
  1. KPI Dashboard  - headline KPIs + engagement segments (live formulas)
  2. Course Summary - per-course comparison + chart (live formulas)
  3. Weekly Trend   - weekly participation trend + chart
  4. At-Risk        - top 50 learners who need intervention (from SQL)
  5. Learner Data   - cleaned learner-level data feeding all formulas

KPI and summary cells are Excel formulas over 'Learner Data', so the report
recalculates if the data is refreshed.
"""
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from config import PROCESSED_DIR, REPORTS_DIR, SQL_RESULTS_DIR, COURSES

FONT = "Arial"
NAVY = "1F3864"
HEADER_FILL = PatternFill("solid", fgColor=NAVY)
KPI_FILL = PatternFill("solid", fgColor="DEEAF6")
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

DATA_COLS = ["learner_id", "name", "city", "course", "engagement_score", "avg_score_pct",
             "assignments_due", "assignments_submitted", "last_active_week",
             "engagement_segment", "dropped_off", "at_risk"]


def style_header(ws, row, c1, c2):
    for c in range(c1, c2 + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(name=FONT, bold=True, color="FFFFFF")
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER


def title(ws, text, sub=None):
    ws["A1"] = text
    ws["A1"].font = Font(name=FONT, size=16, bold=True, color=NAVY)
    if sub:
        ws["A2"] = sub
        ws["A2"].font = Font(name=FONT, size=9, italic=True, color="595959")
    ws.sheet_view.showGridLines = False


def widths(ws, mapping):
    for col, w in mapping.items():
        ws.column_dimensions[col].width = w


def build_data_sheet(wb, df):
    ws = wb.create_sheet("Learner Data")
    ws.append(DATA_COLS)
    for row in df[DATA_COLS].itertuples(index=False):
        ws.append([None if pd.isna(v) else v for v in row])
    style_header(ws, 1, 1, len(DATA_COLS))
    for r in ws.iter_rows(min_row=2):
        for c in r:
            c.font = Font(name=FONT, size=10)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    widths(ws, {"A": 11, "B": 20, "C": 13, "D": 24, "E": 15, "F": 14, "G": 14,
                "H": 17, "I": 15, "J": 18, "K": 11, "L": 9})
    return len(df) + 1          # last data row


def build_kpi_sheet(ws, last):
    title(ws, "Learner Engagement & Performance - KPI Dashboard",
          "All figures are formulas over the 'Learner Data' sheet.")
    D = "'Learner Data'!"
    rng = lambda col: f"{D}${col}$2:${col}${last}"

    kpis = [
        ("Total Learners", f"=COUNTA({rng('A')})", "#,##0"),
        ("Avg Engagement Score (0-100)", f"=AVERAGE({rng('E')})", "0.0"),
        ("Avg Assessment Score (%)", f"=AVERAGE({rng('F')})", "0.0"),
        ("Assignment Completion Rate", f"=SUM({rng('H')})/SUM({rng('G')})", "0.0%"),
        ("Drop-off Rate", f"=SUM({rng('K')})/COUNTA({rng('A')})", "0.0%"),
        ("At-Risk Learners (%)", f"=SUM({rng('L')})/COUNTA({rng('A')})", "0.0%"),
    ]
    ws["A4"], ws["B4"] = "KPI", "Value"
    style_header(ws, 4, 1, 2)
    for i, (name, f, fmt) in enumerate(kpis, start=5):
        ws.cell(row=i, column=1, value=name).font = Font(name=FONT, bold=True)
        v = ws.cell(row=i, column=2, value=f)
        v.number_format, v.font = fmt, Font(name=FONT, size=12, bold=True, color=NAVY)
        for c in (1, 2):
            ws.cell(row=i, column=c).fill = KPI_FILL
            ws.cell(row=i, column=c).border = BORDER

    ws["A13"] = "Engagement Segments"
    ws["A13"].font = Font(name=FONT, bold=True, size=12, color=NAVY)
    for j, h in enumerate(["Segment", "Learners", "% of Total", "Avg Score (%)"], start=1):
        ws.cell(row=14, column=j, value=h)
    style_header(ws, 14, 1, 4)
    for i, seg in enumerate(["High", "Medium", "Low"], start=15):
        ws.cell(row=i, column=1, value=seg)
        ws.cell(row=i, column=2, value=f"=COUNTIF({rng('J')},A{i})")
        ws.cell(row=i, column=3, value=f"=B{i}/$B$5").number_format = "0.0%"
        ws.cell(row=i, column=4, value=f"=AVERAGEIF({rng('J')},A{i},{rng('F')})").number_format = "0.0"
        for c in range(1, 5):
            ws.cell(row=i, column=c).font = Font(name=FONT)
            ws.cell(row=i, column=c).border = BORDER

    ws["A19"] = ("Definitions: Engagement score = 30% active-weeks + 30% assignment completion + "
                 "20% live attendance + 20% watch time. High >= 70, Low < 40. "
                 "Drop-off = no activity in last 3 weeks. At-risk = Low engagement OR dropped off OR avg score < 50%.")
    ws["A19"].font = Font(name=FONT, size=9, italic=True, color="595959")
    ws["A19"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A19:H21")

    ch = BarChart()
    ch.type, ch.title = "col", "Avg Assessment Score by Engagement Segment"
    ch.add_data(Reference(ws, min_col=4, min_row=14, max_row=17), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=15, max_row=17))
    ch.y_axis.title, ch.x_axis.title = "Avg score (%)", "Segment"
    ch.legend = None
    ch.roundedCorners = False
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    ch.height, ch.width = 7.5, 13
    ws.add_chart(ch, "D4")
    widths(ws, {"A": 32, "B": 14, "C": 13, "D": 14})


def build_course_sheet(ws, last):
    title(ws, "Course Summary", "Formulas over 'Learner Data'.")
    D = "'Learner Data'!"
    rng = lambda col: f"{D}${col}$2:${col}${last}"
    heads = ["Course", "Learners", "Avg Engagement", "Avg Score (%)",
             "Drop-off Rate", "At-Risk Rate", "Assignment Completion"]
    for j, h in enumerate(heads, start=1):
        ws.cell(row=4, column=j, value=h)
    style_header(ws, 4, 1, len(heads))
    for i, c in enumerate(COURSES, start=5):
        ws.cell(row=i, column=1, value=c)
        ws.cell(row=i, column=2, value=f"=COUNTIF({rng('D')},A{i})")
        ws.cell(row=i, column=3, value=f"=AVERAGEIF({rng('D')},A{i},{rng('E')})").number_format = "0.0"
        ws.cell(row=i, column=4, value=f"=AVERAGEIF({rng('D')},A{i},{rng('F')})").number_format = "0.0"
        ws.cell(row=i, column=5, value=f"=SUMIF({rng('D')},A{i},{rng('K')})/B{i}").number_format = "0.0%"
        ws.cell(row=i, column=6, value=f"=SUMIF({rng('D')},A{i},{rng('L')})/B{i}").number_format = "0.0%"
        ws.cell(row=i, column=7,
                value=f"=SUMIF({rng('D')},A{i},{rng('H')})/SUMIF({rng('D')},A{i},{rng('G')})").number_format = "0.0%"
        for k in range(1, 8):
            ws.cell(row=i, column=k).font = Font(name=FONT)
            ws.cell(row=i, column=k).border = BORDER
    n = 4 + len(COURSES)
    ch = BarChart()
    ch.type, ch.title = "col", "Avg Engagement Score by Course"
    ch.add_data(Reference(ws, min_col=3, min_row=4, max_row=n), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=5, max_row=n))
    ch.y_axis.title, ch.x_axis.title = "Engagement score", "Course"
    ch.legend = None
    ch.roundedCorners = False
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    ch.height, ch.width = 8, 16
    ws.add_chart(ch, "A11")
    widths(ws, {"A": 26, "B": 11, "C": 16, "D": 14, "E": 14, "F": 13, "G": 22})


def build_weekly_sheet(ws):
    title(ws, "Weekly Participation Trend",
          "Weekly aggregates come from the SQL query 'weekly_engagement_trend' (blue = SQL input); "
          "active rate is a formula.")
    wk = pd.read_csv(SQL_RESULTS_DIR / "weekly_engagement_trend.csv")
    heads = ["Week", "Active Learners", "Total Learners", "Active Rate", "Avg Minutes Watched",
             "Assignment Rate", "Live Attendance"]
    for j, h in enumerate(heads, start=1):
        ws.cell(row=4, column=j, value=h)
    style_header(ws, 4, 1, len(heads))
    blue = Font(name=FONT, color="0000FF")
    for i, r in enumerate(wk.itertuples(index=False), start=5):
        ws.cell(row=i, column=1, value=int(r.week)).font = blue
        ws.cell(row=i, column=2, value=int(r.active_learners)).font = blue
        ws.cell(row=i, column=3, value="='KPI Dashboard'!$B$5").font = Font(name=FONT, color="008000")
        ws.cell(row=i, column=4, value=f"=B{i}/C{i}").number_format = "0.0%"
        ws.cell(row=i, column=5, value=float(r.avg_minutes)).font = blue
        ws.cell(row=i, column=6, value=float(r.assignment_rate_pct) / 100).font = blue
        ws.cell(row=i, column=7, value=float(r.live_attendance_pct) / 100).font = blue
        ws.cell(row=i, column=5).number_format = "0.0"
        ws.cell(row=i, column=6).number_format = "0.0%"
        ws.cell(row=i, column=7).number_format = "0.0%"
        for k in range(1, 8):
            ws.cell(row=i, column=k).border = BORDER
            if k == 4:
                ws.cell(row=i, column=k).font = Font(name=FONT)
    n = 4 + len(wk)
    ch = LineChart()
    ch.title = "Weekly Active Learner Rate"
    ch.add_data(Reference(ws, min_col=4, min_row=4, max_row=n), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=5, max_row=n))
    ch.y_axis.title, ch.x_axis.title = "Active rate", "Week"
    ch.y_axis.number_format = "0%"
    ch.legend = None
    ch.roundedCorners = False
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    ch.height, ch.width = 8, 16
    ws.add_chart(ch, "A19")
    widths(ws, {"A": 8, "B": 16, "C": 15, "D": 12, "E": 20, "F": 16, "G": 16})


def build_risk_sheet(ws):
    title(ws, "At-Risk Learners - Top 50 for Intervention",
          "Source: SQL query 'at_risk_learners' (lowest engagement first).")
    df = pd.read_csv(SQL_RESULTS_DIR / "at_risk_learners.csv")
    for j, h in enumerate(df.columns, start=1):
        ws.cell(row=4, column=j, value=h.replace("_", " ").title())
    style_header(ws, 4, 1, len(df.columns))
    fills = {"Critical": "F8CBAD", "High": "FFE699", "Moderate": "E2EFDA"}
    for i, row in enumerate(df.itertuples(index=False), start=5):
        for j, v in enumerate(row, start=1):
            c = ws.cell(row=i, column=j, value=None if pd.isna(v) else v)
            c.font, c.border = Font(name=FONT), BORDER
        ws.cell(row=i, column=len(df.columns)).fill = PatternFill("solid", fgColor=fills[row[-1]])
    ws.freeze_panes = "A5"
    widths(ws, {"A": 11, "B": 20, "C": 24, "D": 13, "E": 17, "F": 15, "G": 17, "H": 12})


def main():
    REPORTS_DIR.mkdir(exist_ok=True)
    df = pd.read_csv(PROCESSED_DIR / "learner_summary.csv")
    wb = Workbook()
    kpi = wb.active
    kpi.title = "KPI Dashboard"
    course, weekly, risk = (wb.create_sheet(n) for n in ["Course Summary", "Weekly Trend", "At-Risk"])
    last = build_data_sheet(wb, df)
    build_kpi_sheet(kpi, last)
    build_course_sheet(course, last)
    build_weekly_sheet(weekly)
    build_risk_sheet(risk)
    out = REPORTS_DIR / "learner_engagement_kpi_report.xlsx"
    wb.save(out)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
