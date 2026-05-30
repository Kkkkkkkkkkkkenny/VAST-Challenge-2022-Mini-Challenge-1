#!/usr/bin/env python3
"""
VAST Challenge 2022 MC1 - Data Processing Pipeline
Processes raw CSV data and produces aggregated parquet files.

Uses chunked reading + vectorized groupby operations for efficiency.
"""

import os
import sys
import glob
import time
import warnings
from collections import defaultdict, Counter

import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

BASE_DIR = "/mnt/d/homework/visulization/finalwork/VAST-Challenge-2022"
DATASETS_DIR = os.path.join(BASE_DIR, "Datasets")
ACTIVITY_DIR = os.path.join(DATASETS_DIR, "Activity Logs")
JOURNALS_DIR = os.path.join(DATASETS_DIR, "Journals")
ATTR_DIR = os.path.join(DATASETS_DIR, "Attributes")
OUTPUT_DIR = os.path.join(BASE_DIR, "processed")

os.makedirs(OUTPUT_DIR, exist_ok=True)

CHUNK_SIZE = 500000  # rows per chunk for activity logs

# =============================================================================
# Helper functions
# =============================================================================
def parse_point(col):
    """Parse POINT(x y) or POINT (x y) string into (x, y) floats."""
    if isinstance(col, str):
        col = col.strip()
        if col.upper().startswith("POINT"):
            col = col[5:].strip().strip("()")
            parts = col.split()
            if len(parts) >= 2:
                return float(parts[0]), float(parts[1])
    return np.nan, np.nan


# =============================================================================
# 1. ACTIVITY LOGS - Chunked + Vectorized
# =============================================================================
def process_activity_logs():
    """
    Process all 72 activity log files with chunked + vectorized operations.
    Returns aggregated DataFrames for participant, hourly, and daily views.
    """
    log_files = sorted(
        glob.glob(os.path.join(ACTIVITY_DIR, "ParticipantStatusLogs*.csv")),
        key=lambda x: int(''.join(filter(str.isdigit, os.path.basename(x))) or 0),
    )
    print(f"Found {len(log_files)} activity log files to process")

    # Participant accumulators (for participant_summary)
    part_agg = defaultdict(lambda: {
        "balance_sum": 0.0,
        "count": 0,
        "mode_counts": Counter(),
        "fin_status_counts": Counter(),
    })

    # Hourly accumulators
    hourly_mode = defaultdict(Counter)       # hour -> {mode: count}
    hourly_hunger = defaultdict(Counter)     # hour -> {hungerStatus: count}
    hourly_sleep = defaultdict(Counter)      # hour -> {sleepStatus: count}

    # Daily accumulators
    daily_mode = defaultdict(Counter)        # day -> {mode: count}
    daily_balance_sum = defaultdict(float)
    daily_count = defaultdict(int)

    total_rows = 0
    start_time = time.time()

    dtype_spec = {
        "participantId": "float32",  # float to handle NA rows (file 72 has trailing NA)
        "currentMode": "str",
        "hungerStatus": "str",
        "sleepStatus": "str",
        "availableBalance": "float32",
        "financialStatus": "str",
        "currentLocation": "str",
        "apartmentId": "str",
        "jobId": "str",
        "dailyFoodBudget": "str",
        "weeklyExtraBudget": "str",
    }

    for file_idx, fpath in enumerate(log_files):
        fname = os.path.basename(fpath)
        chunk_iter = pd.read_csv(
            fpath,
            dtype=dtype_spec,
            parse_dates=["timestamp"],
            chunksize=CHUNK_SIZE,
            low_memory=False,
        )

        for chunk_idx, chunk in enumerate(chunk_iter):
            chunk = chunk.dropna(subset=["participantId", "timestamp"])
            if len(chunk) == 0:
                continue
            chunk["participantId"] = chunk["participantId"].astype("int32")
            p_grp = chunk.groupby("participantId", sort=False)
            part_balance_sum = p_grp["availableBalance"].sum()
            part_count = p_grp.size()

            # ----- Vectorized hourly aggregation -----
            chunk["hour"] = chunk["timestamp"].dt.floor("h")
            chunk["day"] = chunk["timestamp"].dt.date

            # Hourly mode counts
            hm = chunk.groupby(["hour", "currentMode"], sort=False).size()
            for (hr, mode), cnt in hm.items():
                hourly_mode[hr][mode] += cnt

            # Hourly hunger counts
            hh = chunk.groupby(["hour", "hungerStatus"], sort=False).size()
            for (hr, status), cnt in hh.items():
                hourly_hunger[hr][status] += cnt

            # Hourly sleep counts
            hs = chunk.groupby(["hour", "sleepStatus"], sort=False).size()
            for (hr, status), cnt in hs.items():
                hourly_sleep[hr][status] += cnt

            # Daily mode counts
            dm = chunk.groupby(["day", "currentMode"], sort=False).size()
            for (day, mode), cnt in dm.items():
                daily_mode[day][mode] += cnt

            # Daily balance sum & count
            db = chunk.groupby("day", sort=False)["availableBalance"].sum()
            dc = chunk.groupby("day", sort=False).size()
            for day, bal in db.items():
                daily_balance_sum[day] += bal
            for day, cnt in dc.items():
                daily_count[day] += cnt

            # Update participant accumulators (using iterrows on groups, not raw rows)
            # Number of groups = number of participants (~1010), which is tiny
            for pid, bal_sum in part_balance_sum.items():
                part_agg[pid]["balance_sum"] += bal_sum
            for pid, cnt in part_count.items():
                part_agg[pid]["count"] += cnt

            # Mode counts per participant
            p_mode = chunk.groupby(["participantId", "currentMode"], sort=False).size()
            for (pid, mode), cnt in p_mode.items():
                part_agg[pid]["mode_counts"][mode] += cnt

            # Fin status per participant
            p_fin = chunk.groupby(["participantId", "financialStatus"], sort=False).size()
            for (pid, fs), cnt in p_fin.items():
                part_agg[pid]["fin_status_counts"][fs] += cnt

            total_rows += len(chunk)

            if (chunk_idx + 1) % 5 == 0:
                elapsed = time.time() - start_time
                rate = total_rows / elapsed if elapsed > 0 else 0
                print(
                    f"  [{fname}] chunk {chunk_idx + 1}, "
                    f"{total_rows:,} rows, {rate:,.0f} rows/s"
                )

        print(f"  [{file_idx + 1}/{len(log_files)}] {fname} done "
              f"(total: {total_rows:,})")

    elapsed = time.time() - start_time
    print(f"Activity logs: {total_rows:,} rows in {elapsed:.1f}s "
          f"({total_rows/elapsed:,.0f} rows/s avg)")

    # --- Build participant activity summary ---
    part_rows = []
    for pid, agg in part_agg.items():
        avg_bal = agg["balance_sum"] / agg["count"] if agg["count"] > 0 else 0
        primary_mode = max(agg["mode_counts"], key=agg["mode_counts"].get) if agg["mode_counts"] else None
        primary_fin = max(agg["fin_status_counts"], key=agg["fin_status_counts"].get) if agg["fin_status_counts"] else None
        part_rows.append({
            "participantId": pid,
            "avg_availableBalance": round(avg_bal, 2),
            "primary_mode": primary_mode,
            "primary_financialStatus": primary_fin,
            "total_activity_records": agg["count"],
        })
    df_part_act = pd.DataFrame(part_rows).sort_values("participantId").reset_index(drop=True)

    # --- Build hourly activity ---
    hourly_rows = []
    for hr in sorted(hourly_mode.keys()):
        row = {"hour": hr}
        for m in ["AtHome", "AtWork", "Transport", "Recreation", "Eating"]:
            row[f"mode_{m}"] = hourly_mode[hr].get(m, 0)
        for s in ["JustAte", "Hungry", "Starving"]:
            row[f"hunger_{s}"] = hourly_hunger[hr].get(s, 0)
        for s in ["Sleeping", "Tired", "Awake", "WellRested"]:
            row[f"sleep_{s}"] = hourly_sleep[hr].get(s, 0)
        hourly_rows.append(row)
    df_hourly = pd.DataFrame(hourly_rows)

    # --- Build daily activity ---
    daily_rows = []
    for day in sorted(daily_mode.keys()):
        row = {"day": pd.Timestamp(day)}
        for m in ["AtHome", "AtWork", "Transport", "Recreation", "Eating"]:
            row[f"mode_{m}"] = daily_mode[day].get(m, 0)
        row["total_count"] = daily_count.get(day, 0)
        row["avg_balance"] = round(
            daily_balance_sum.get(day, 0) / daily_count.get(day, 1), 2
        )
        daily_rows.append(row)
    df_daily = pd.DataFrame(daily_rows)

    return df_part_act, df_hourly, df_daily


# =============================================================================
# 2. ATTRIBUTES
# =============================================================================
def load_attributes():
    """Load all attribute CSV files and parse venue coordinates."""
    participants = pd.read_csv(os.path.join(ATTR_DIR, "Participants.csv"))
    apartments = pd.read_csv(os.path.join(ATTR_DIR, "Apartments.csv"))
    employers = pd.read_csv(os.path.join(ATTR_DIR, "Employers.csv"))
    jobs = pd.read_csv(os.path.join(ATTR_DIR, "Jobs.csv"))
    pubs = pd.read_csv(os.path.join(ATTR_DIR, "Pubs.csv"))
    restaurants = pd.read_csv(os.path.join(ATTR_DIR, "Restaurants.csv"))
    schools = pd.read_csv(os.path.join(ATTR_DIR, "Schools.csv"))
    buildings = pd.read_csv(os.path.join(ATTR_DIR, "Buildings.csv"))

    # Parse coordinates for venues
    for df in [pubs, restaurants, schools, apartments]:
        coords = df["location"].apply(parse_point)
        df["x"] = coords.apply(lambda c: c[0])
        df["y"] = coords.apply(lambda c: c[1])

    print(f"Attributes: Participants={len(participants)}, Apartments={len(apartments)}, "
          f"Employers={len(employers)}, Jobs={len(jobs)}, Pubs={len(pubs)}, "
          f"Restaurants={len(restaurants)}, Schools={len(schools)}, Buildings={len(buildings)}")
    return participants, apartments, employers, jobs, pubs, restaurants, schools, buildings


# =============================================================================
# 3. JOURNALS
# =============================================================================
def process_checkin_journal():
    """CheckinJournal -> venue checkin counts."""
    print("  CheckinJournal...", end=" ", flush=True)
    start = time.time()
    chunks = pd.read_csv(
        os.path.join(JOURNALS_DIR, "CheckinJournal.csv"),
        usecols=["venueId", "venueType"],
        chunksize=500000,
    )
    venue_counts = Counter()
    total = 0
    for chunk in chunks:
        for _, row in chunk.iterrows():
            venue_counts[(row["venueId"], row["venueType"])] += 1
        total += len(chunk)
    rows = [
        {"venueId": vid, "venueType": vt, "checkins": cnt}
        for (vid, vt), cnt in venue_counts.most_common()
    ]
    print(f"{total:,} records, {len(rows)} venues, {time.time()-start:.1f}s")
    return pd.DataFrame(rows)


def process_financial_journal():
    """FinancialJournal -> financial_summary + daily_financial."""
    print("  FinancialJournal...", end=" ", flush=True)
    start = time.time()
    chunks = pd.read_csv(
        os.path.join(JOURNALS_DIR, "FinancialJournal.csv"),
        parse_dates=["timestamp"],
        chunksize=500000,
    )
    cat_sum = defaultdict(float)
    cat_count = defaultdict(int)
    daily_cat_sum = defaultdict(float)
    total = 0
    for chunk in chunks:
        chunk["day"] = chunk["timestamp"].dt.date
        for _, row in chunk.iterrows():
            cat = row["category"]
            amt = row["amount"]
            cat_sum[cat] += amt
            cat_count[cat] += 1
            daily_cat_sum[(row["day"], cat)] += amt
            total += 1

    fin_rows = [
        {"category": c, "total_amount": round(cat_sum[c], 2),
         "avg_amount": round(cat_sum[c] / cat_count[c], 2),
         "transaction_count": cat_count[c]}
        for c in sorted(cat_sum.keys())
    ]
    daily_rows = [
        {"day": pd.Timestamp(d), "category": c, "total_amount": round(amt, 2)}
        for (d, c), amt in sorted(daily_cat_sum.items())
    ]
    print(f"{total:,} records, {len(fin_rows)} categories, {time.time()-start:.1f}s")
    return pd.DataFrame(fin_rows), pd.DataFrame(daily_rows)


def process_social_network():
    """SocialNetwork -> edge list with weights."""
    print("  SocialNetwork...", end=" ", flush=True)
    start = time.time()
    chunks = pd.read_csv(
        os.path.join(JOURNALS_DIR, "SocialNetwork.csv"),
        usecols=["participantIdFrom", "participantIdTo"],
        dtype={"participantIdFrom": "int32", "participantIdTo": "int32"},
        chunksize=500000,
    )
    edge_weights = Counter()
    total = 0
    for chunk in chunks:
        for _, row in chunk.iterrows():
            edge_weights[(row["participantIdFrom"], row["participantIdTo"])] += 1
        total += len(chunk)
    rows = [
        {"participantIdFrom": frm, "participantIdTo": to, "weight": w}
        for (frm, to), w in edge_weights.most_common()
    ]
    print(f"{total:,} records, {len(rows)} edges, {time.time()-start:.1f}s")
    return pd.DataFrame(rows)


def process_travel_journal():
    """TravelJournal -> travel purpose summary."""
    print("  TravelJournal...", end=" ", flush=True)
    start = time.time()
    chunks = pd.read_csv(
        os.path.join(JOURNALS_DIR, "TravelJournal.csv"),
        usecols=["purpose", "startingBalance", "endingBalance"],
        chunksize=500000,
    )
    purpose_counts = Counter()
    purpose_cost = defaultdict(float)
    total = 0
    for chunk in chunks:
        chunk["startingBalance"] = pd.to_numeric(chunk["startingBalance"], errors="coerce")
        chunk["endingBalance"] = pd.to_numeric(chunk["endingBalance"], errors="coerce")
        for _, row in chunk.iterrows():
            p = row["purpose"]
            purpose_counts[p] += 1
            if pd.notna(row["startingBalance"]) and pd.notna(row["endingBalance"]):
                purpose_cost[p] += row["startingBalance"] - row["endingBalance"]
        total += len(chunk)
    rows = [
        {"purpose": p, "count": cnt, "total_spent": round(purpose_cost.get(p, 0), 2)}
        for p, cnt in purpose_counts.most_common()
    ]
    print(f"{total:,} records, {len(rows)} purposes, {time.time()-start:.1f}s")
    return pd.DataFrame(rows)


# =============================================================================
# 4. JOB / EMPLOYER SUMMARIES
# =============================================================================
def build_job_summaries(jobs_df):
    """From Jobs.csv, produce job_summary and employer_summary."""
    jobs_df["hourlyRate"] = pd.to_numeric(jobs_df["hourlyRate"], errors="coerce")

    # Job summary
    df_jobs = jobs_df[["jobId", "employerId", "hourlyRate", "educationRequirement"]].copy()

    # Employer summary
    df_emp = jobs_df.groupby("employerId", sort=False).agg(
        employee_count=("jobId", "count"),
        avg_hourlyRate=("hourlyRate", "mean"),
        min_hourlyRate=("hourlyRate", "min"),
        max_hourlyRate=("hourlyRate", "max"),
    ).reset_index()
    df_emp["avg_hourlyRate"] = df_emp["avg_hourlyRate"].round(2)

    print(f"  Jobs: {len(df_jobs)}, Employers: {len(df_emp)}")
    return df_jobs, df_emp


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("=" * 60)
    print("VAST Challenge 2022 MC1 - Data Processing Pipeline")
    print("=" * 60)
    total_start = time.time()

    # ---- Step 1: Activity Logs ----
    print("\n[1/5] Processing Activity Logs (114M rows)...")
    t0 = time.time()
    df_part_act, df_hourly, df_daily = process_activity_logs()
    print(f"  Time: {time.time()-t0:.1f}s")

    # ---- Step 2: Attributes ----
    print("\n[2/5] Loading Attributes...")
    t0 = time.time()
    participants, apartments, employers, jobs, pubs, restaurants, schools, buildings = load_attributes()
    print(f"  Time: {time.time()-t0:.1f}s")

    # ---- Step 3: Merge Participant Summary ----
    print("\n[3/5] Building Participant Summary...")
    t0 = time.time()
    df_participant = participants.merge(
        df_part_act, on="participantId", how="left"
    )
    # Add social degree from later processing
    print(f"  {len(df_participant)} participants")
    print(f"  Time: {time.time()-t0:.1f}s")

    # ---- Step 4: Process Journals ----
    print("\n[4/5] Processing Journals...")
    t0 = time.time()
    df_venue = process_checkin_journal()
    df_fin, df_daily_fin = process_financial_journal()
    df_social = process_social_network()
    df_travel = process_travel_journal()
    print(f"  Total journal time: {time.time()-t0:.1f}s")

    # ---- Step 5: Build & Save ----
    print("\n[5/5] Building Job Summaries & Saving...")
    t0 = time.time()
    df_jobs, df_emp = build_job_summaries(jobs)

    # Building types summary
    building_types = buildings["buildingType"].value_counts().reset_index()
    building_types.columns = ["buildingType", "count"]

    # Enrich participant summary with social degree
    social_degree_in = df_social.groupby("participantIdFrom").agg(
        total_interactions=("weight", "sum"),
        unique_contacts=("participantIdTo", "count"),
    ).reset_index().rename(columns={"participantIdFrom": "participantId"})
    social_degree_out = df_social.groupby("participantIdTo").agg(
        total_interactions_received=("weight", "sum"),
        unique_contacts_from=("participantIdFrom", "count"),
    ).reset_index().rename(columns={"participantIdTo": "participantId"})
    df_participant = df_participant.merge(social_degree_in, on="participantId", how="left")
    df_participant = df_participant.merge(social_degree_out, on="participantId", how="left")
    df_participant = df_participant.fillna(0)
    df_participant["total_social_interactions"] = (
        df_participant["total_interactions"] + df_participant["total_interactions_received"]
    ).astype(int)

    # Alias columns for app.py compatibility
    df_participant["avg_balance"] = df_participant["avg_availableBalance"]
    df_participant["social_degree"] = df_participant["total_social_interactions"]

    # Save all parquet files
    outputs = {
        "participant_summary.parquet": df_participant,
        "hourly_activity.parquet": df_hourly,
        "daily_activity.parquet": df_daily,
        "venue_checkins.parquet": df_venue,
        "financial_summary.parquet": df_fin,
        "daily_financial.parquet": df_daily_fin,
        "social_network.parquet": df_social,
        "travel_purpose_summary.parquet": df_travel,
        "job_summary.parquet": df_emp.rename(columns={"avg_hourlyRate": "avg_hourly_rate"}),
        "building_types.parquet": building_types,
        "pubs.parquet": pubs[["pubId", "hourlyCost", "maxOccupancy", "x", "y", "buildingId"]],
        "restaurants.parquet": restaurants[["restaurantId", "foodCost", "maxOccupancy ", "x", "y", "buildingId"]].rename(columns={"maxOccupancy ": "maxOccupancy"}),
        "schools.parquet": schools[["schoolId", "monthlyCost", "maxEnrollment", "x", "y", "buildingId"]],
        "apartments.parquet": apartments[["apartmentId", "rentalCost", "maxOccupancy ", "numberOfRooms", "x", "y", "buildingId"]].rename(columns={"maxOccupancy ": "maxOccupancy"}),
    }

    for fname, df in outputs.items():
        fpath = os.path.join(OUTPUT_DIR, fname)
        df.to_parquet(fpath, index=False, engine="fastparquet")
        mb = os.path.getsize(fpath) / (1024 * 1024)
        print(f"  {fname}: {len(df):>8,} rows, {mb:>7.1f} MB")

    print(f"\n  Save time: {time.time()-t0:.1f}s")
    total_elapsed = time.time() - total_start
    print(f"\n{'=' * 60}")
    print(f"ALL DONE in {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
