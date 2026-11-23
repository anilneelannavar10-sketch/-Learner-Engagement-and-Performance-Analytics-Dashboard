"""
Step 2 - Data cleaning and transformation with Pandas.

Reads raw CSVs from data/raw/, fixes data-quality issues, engineers features
(engagement score, segments, risk flags) and writes tidy CSVs to data/processed/.
"""
import numpy as np
import pandas as pd
from config import (RAW_DIR, PROCESSED_DIR, COURSES, WEIGHTS, WATCH_TARGET_MIN_PER_WEEK,
                    HIGH_ENGAGEMENT, LOW_ENGAGEMENT, LOW_SCORE_PCT)


# ----------------------------------------------------------------- cleaning
def clean_learners(df):
    n0 = len(df)
    df = df.copy()
    df["learner_id"] = df["learner_id"].str.strip().str.upper()
    df["name"] = df["name"].str.strip().str.title()

    # standardise course names: ignore case/spaces, map back to the official label
    lookup = {c.replace(" ", "").lower(): c for c in COURSES}
    df["course"] = df["course"].str.replace(" ", "", regex=False).str.lower().map(lookup)

    df["city"] = df["city"].str.strip().str.title().fillna("Unknown")
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")
    df["signup_date"] = df["signup_date"].fillna(df["signup_date"].median())

    df = df.drop_duplicates("learner_id").dropna(subset=["course"])
    print(f"[learners]    {n0} -> {len(df)} rows")
    return df.reset_index(drop=True)


def clean_engagement(df, valid_ids):
    n0 = len(df)
    df = df.drop_duplicates(["learner_id", "week"]).copy()
    df["learner_id"] = df["learner_id"].str.strip().str.upper()
    df = df[df["learner_id"].isin(valid_ids)]

    num_cols = ["sessions", "minutes_watched", "assignments_submitted"]
    df.loc[df["minutes_watched"] < 0, "minutes_watched"] = np.nan   # impossible values

    # impute missing values with the median of that week (robust to outliers)
    for c in num_cols:
        df[c] = df[c].fillna(df.groupby("week")[c].transform("median"))
        df[c] = df[c].round().astype(int)

    # business rule: cannot submit more than what was due
    df["assignments_submitted"] = df[["assignments_submitted", "assignments_due"]].min(axis=1)
    df["is_active"] = (df["sessions"] > 0).astype(int)
    print(f"[engagement]  {n0} -> {len(df)} rows")
    return df.reset_index(drop=True)


def clean_assessments(df, valid_ids):
    n0 = len(df)
    df = df.drop_duplicates(["learner_id", "assessment"]).copy()
    df["learner_id"] = df["learner_id"].str.strip().str.upper()
    df = df[df["learner_id"].isin(valid_ids)].dropna(subset=["score"])
    df["score"] = df[["score", "max_score"]].min(axis=1)             # cap at max
    df["score_pct"] = (df["score"] / df["max_score"] * 100).round(1)
    print(f"[assessments] {n0} -> {len(df)} rows")
    return df.reset_index(drop=True)


# ---------------------------------------------------------- transformation
def build_learner_summary(learners, eng, ass):
    agg = eng.groupby("learner_id").agg(
        total_sessions=("sessions", "sum"),
        total_minutes=("minutes_watched", "sum"),
        weeks_tracked=("week", "nunique"),
        active_weeks=("is_active", "sum"),
        assignments_due=("assignments_due", "sum"),
        assignments_submitted=("assignments_submitted", "sum"),
        live_scheduled=("live_classes_scheduled", "sum"),
        live_attended=("live_classes_attended", "sum"),
        forum_posts=("forum_posts", "sum"),
    ).reset_index()

    agg["active_weeks_rate"] = agg["active_weeks"] / agg["weeks_tracked"]
    agg["assignment_rate"] = agg["assignments_submitted"] / agg["assignments_due"]
    agg["live_attendance_rate"] = agg["live_attended"] / agg["live_scheduled"]
    agg["avg_weekly_minutes"] = agg["total_minutes"] / agg["weeks_tracked"]
    agg["watch_time_rate"] = (agg["avg_weekly_minutes"] / WATCH_TARGET_MIN_PER_WEEK).clip(upper=1)

    agg["engagement_score"] = (sum(agg[k] * w for k, w in WEIGHTS.items()) * 100).round(1)

    # last week in which the learner was active -> drop-off indicator
    last_active = (eng[eng["is_active"] == 1].groupby("learner_id")["week"].max()
                   .rename("last_active_week"))
    agg = agg.merge(last_active, on="learner_id", how="left")
    agg["last_active_week"] = agg["last_active_week"].fillna(0).astype(int)

    score = ass.groupby("learner_id").agg(
        avg_score_pct=("score_pct", "mean"),
        assessments_taken=("assessment", "count")).reset_index()
    score["avg_score_pct"] = score["avg_score_pct"].round(1)

    out = learners.merge(agg, on="learner_id", how="left").merge(score, on="learner_id", how="left")
    out["assessments_taken"] = out["assessments_taken"].fillna(0).astype(int)

    out["engagement_segment"] = pd.cut(
        out["engagement_score"], [-1, LOW_ENGAGEMENT, HIGH_ENGAGEMENT, 101],
        labels=["Low", "Medium", "High"]).astype(str)

    max_week = eng["week"].max()
    out["dropped_off"] = (out["last_active_week"] < max_week - 2).astype(int)
    out["at_risk"] = (
        (out["engagement_segment"] == "Low")
        | (out["dropped_off"] == 1)
        | (out["avg_score_pct"].fillna(0) < LOW_SCORE_PCT)
    ).astype(int)

    num = out.select_dtypes("number").columns
    out[num] = out[num].round(3)
    return out


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    learners = clean_learners(pd.read_csv(RAW_DIR / "learners_raw.csv"))
    ids = set(learners["learner_id"])
    eng = clean_engagement(pd.read_csv(RAW_DIR / "engagement_raw.csv"), ids)
    ass = clean_assessments(pd.read_csv(RAW_DIR / "assessments_raw.csv"), ids)
    summary = build_learner_summary(learners, eng, ass)

    learners.to_csv(PROCESSED_DIR / "learners_clean.csv", index=False)
    eng.to_csv(PROCESSED_DIR / "engagement_clean.csv", index=False)
    ass.to_csv(PROCESSED_DIR / "assessments_clean.csv", index=False)
    summary.to_csv(PROCESSED_DIR / "learner_summary.csv", index=False)
    print(f"[summary]     {len(summary)} learners | at risk: {summary['at_risk'].sum()}")


if __name__ == "__main__":
    main()
