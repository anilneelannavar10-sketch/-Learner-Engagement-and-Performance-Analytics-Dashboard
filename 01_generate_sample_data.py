"""
Step 1 - Generate a realistic, deliberately messy sample dataset.

Real learner data is not shared publicly, so this script simulates three raw
tables (learners, weekly engagement, assessments) with common data-quality
problems: duplicates, missing values, inconsistent text, negative numbers,
and bad dates. Replace the CSVs in data/raw/ with real exports to reuse the
pipeline.
"""
import numpy as np
import pandas as pd
from config import RAW_DIR, COURSES, N_LEARNERS, N_WEEKS, SEED


def build_learners(rng):
    cities = ["Bengaluru", "Hyderabad", "Pune", "Delhi", "Chennai", "Mumbai", "Kolkata"]
    first = ["Aarav", "Diya", "Rohan", "Isha", "Kabir", "Ananya", "Vihaan", "Meera",
             "Arjun", "Sneha", "Karan", "Priya", "Aditya", "Neha", "Rahul", "Pooja"]
    last = ["Sharma", "Reddy", "Patel", "Nair", "Singh", "Iyer", "Gupta", "Das", "Mehta", "Rao"]
    ids = [f"L{1000 + i}" for i in range(N_LEARNERS)]
    df = pd.DataFrame({
        "learner_id": ids,
        "name": [f"{rng.choice(first)} {rng.choice(last)}" for _ in ids],
        "city": rng.choice(cities, N_LEARNERS),
        "course": rng.choice(COURSES, N_LEARNERS, p=[0.30, 0.30, 0.20, 0.20]),
        "signup_date": pd.to_datetime("2025-01-06")
        + pd.to_timedelta(rng.integers(0, 28, N_LEARNERS), unit="D"),
    })
    # latent motivation drives engagement + scores later
    df["_motivation"] = np.clip(rng.beta(2.2, 1.8, N_LEARNERS), 0.05, 1)
    return df


def build_engagement(learners, rng):
    rows = []
    for _, l in learners.iterrows():
        m = l["_motivation"]
        dropped_at = N_WEEKS + 1
        if m < 0.35 and rng.random() < 0.7:          # churners
            dropped_at = int(rng.integers(3, 9))
        for w in range(1, N_WEEKS + 1):
            decay = 1 - 0.025 * w
            active = w < dropped_at and rng.random() < (0.35 + 0.65 * m)
            sessions = int(rng.poisson(5 * m * decay)) if active else 0
            rows.append({
                "learner_id": l["learner_id"],
                "week": w,
                "sessions": sessions,
                "minutes_watched": int(max(0, rng.normal(60 * sessions, 20))) if sessions else 0,
                "assignments_due": 3,
                "assignments_submitted": min(3, int(rng.binomial(3, 0.15 + 0.8 * m))) if active else 0,
                "live_classes_scheduled": 2,
                "live_classes_attended": int(rng.binomial(2, 0.1 + 0.85 * m)) if active else 0,
                "forum_posts": int(rng.poisson(1.5 * m)) if active else 0,
            })
    return pd.DataFrame(rows)


def build_assessments(learners, rng):
    names = {"Quiz 1": 20, "Quiz 2": 20, "Mid-term": 50, "Final": 100}
    rows = []
    for _, l in learners.iterrows():
        m = l["_motivation"]
        for a, mx in names.items():
            if rng.random() < 0.08 + (0.35 if m < 0.3 else 0):   # skipped
                continue
            pct = np.clip(rng.normal(35 + 55 * m, 9), 5, 100)
            rows.append({"learner_id": l["learner_id"], "assessment": a,
                         "score": round(pct / 100 * mx, 1), "max_score": mx})
    return pd.DataFrame(rows)


def add_mess(learners, engagement, assessments, rng):
    # --- learners: inconsistent text, whitespace, bad dates, duplicates
    learners = learners.copy()
    learners["course"] = learners["course"].apply(
        lambda c: rng.choice([c, c.upper(), c.lower(), f" {c} ", c.replace(" ", "")],
                             p=[.7, .08, .08, .08, .06]))
    learners["name"] = learners["name"].apply(lambda n: n.lower() if rng.random() < 0.1 else n)
    learners["signup_date"] = learners["signup_date"].dt.strftime("%Y-%m-%d")
    bad = rng.choice(learners.index, 8, replace=False)
    learners.loc[bad, "signup_date"] = "not available"
    learners.loc[rng.choice(learners.index, 15, replace=False), "city"] = np.nan
    learners = pd.concat([learners, learners.sample(12, random_state=1)], ignore_index=True)

    # --- engagement: missing values, negatives, duplicates
    engagement = engagement.copy()
    for col in ["sessions", "minutes_watched", "assignments_submitted"]:
        engagement.loc[rng.choice(engagement.index, 60, replace=False), col] = np.nan
    engagement.loc[rng.choice(engagement.index, 20, replace=False), "minutes_watched"] = -1
    engagement = pd.concat([engagement, engagement.sample(40, random_state=2)], ignore_index=True)

    # --- assessments: scores above max, missing scores, duplicates
    assessments = assessments.copy()
    idx = rng.choice(assessments.index, 10, replace=False)
    assessments.loc[idx, "score"] = assessments.loc[idx, "max_score"] + 5
    assessments.loc[rng.choice(assessments.index, 15, replace=False), "score"] = np.nan
    assessments = pd.concat([assessments, assessments.sample(10, random_state=3)], ignore_index=True)
    return learners, engagement, assessments


def main():
    rng = np.random.default_rng(SEED)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    learners = build_learners(rng)
    engagement = build_engagement(learners, rng)
    assessments = build_assessments(learners, rng)
    learners, engagement, assessments = add_mess(
        learners.drop(columns="_motivation"), engagement, assessments, rng)

    learners.to_csv(RAW_DIR / "learners_raw.csv", index=False)
    engagement.to_csv(RAW_DIR / "engagement_raw.csv", index=False)
    assessments.to_csv(RAW_DIR / "assessments_raw.csv", index=False)
    print(f"learners_raw.csv     : {len(learners):>6} rows")
    print(f"engagement_raw.csv   : {len(engagement):>6} rows")
    print(f"assessments_raw.csv  : {len(assessments):>6} rows")


if __name__ == "__main__":
    main()
