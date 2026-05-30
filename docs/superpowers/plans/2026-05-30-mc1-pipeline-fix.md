# MC1 Data Pipeline Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the MC1 data pipeline so `process_data.py` outputs all data `app.py` needs with matching column names, then run processing and verify the dashboard works.

**Architecture:** Keep `process_data.py`'s efficient Counter/dict-based chunked processing (memory-safe for 100M+ rows), fix column names and add missing venue/building outputs to align with `app.py`'s expectations. Update `app.py` to read `.parquet` instead of `.pkl`.

**Tech Stack:** Python 3, pandas, fastparquet, Streamlit, Plotly

---

## Column Name Mapping

| Data File | process_data.py column | app.py expects | Action |
|-----------|----------------------|----------------|--------|
| venue_checkins | `checkin_count` | `checkins` | Rename |
| travel_purpose_summary | `trip_count` | `count` | Rename |
| travel_purpose_summary | `total_balance_change` | `total_spent` | Rename |
| participant_summary | `avg_availableBalance` | `avg_balance` | Add alias column |
| participant_summary | `total_social_interactions` | `social_degree` | Add alias column |
| job_summary | (per-job data) | (per-employer data) | Use employer_summary as job_summary |
| employer_summary | `avg_hourlyRate` | `avg_hourly_rate` | Rename |

## Missing Outputs to Add

- `building_types.parquet` — from Buildings.csv aggregation
- `pubs.parquet` — with x, y coordinates parsed
- `restaurants.parquet` — with x, y coordinates parsed
- `schools.parquet` — with x, y coordinates parsed

---

### Task 1: Delete redundant `data_processor.py` and empty `processed/`

**Files:**
- Delete: `data_processor.py`

- [ ] **Step 1: Remove redundant file**

```bash
rm /mnt/d/homework/visulization/finalwork/VAST-Challenge-2022/data_processor.py
```

- [ ] **Step 2: Commit**

```bash
git add data_processor.py
git commit -m "chore: remove redundant data_processor.py (replaced by process_data.py)"
```

---

### Task 2: Add missing data outputs to `process_data.py`

**Files:**
- Modify: `process_data.py`

Changes:
1. Add `parse_point` helper (already exists in the file, reuse it)
2. In `load_attributes()`, also load Buildings.csv and parse venue coordinates
3. In `main()`, add building_types and venue DataFrames to outputs

- [ ] **Step 1: Update `load_attributes()` to load more data**

Change the function to also load Buildings, and parse coordinates for all venues. Replace the existing `load_attributes` function:

```python
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
```

- [ ] **Step 2: Update `main()` call site to receive new return values**

Change:
```python
participants, apartments, employers, jobs = load_attributes()
```
to:
```python
participants, apartments, employers, jobs, pubs, restaurants, schools, buildings = load_attributes()
```

- [ ] **Step 3: Add building_types creation after the job summaries section**

After the `build_job_summaries` call, add:

```python
    # Building types summary
    building_types = buildings["buildingType"].value_counts().reset_index()
    building_types.columns = ["buildingType", "count"]
```

- [ ] **Step 4: Add venue DataFrames to outputs dict**

In the outputs dict, add these entries:

```python
        "building_types.parquet": building_types,
        "pubs.parquet": pubs[["pubId", "hourlyCost", "maxOccupancy", "x", "y", "buildingId"]],
        "restaurants.parquet": restaurants[["restaurantId", "foodCost", "maxOccupancy", "x", "y", "buildingId"]],
        "schools.parquet": schools[["schoolId", "monthlyCost", "maxEnrollment", "x", "y", "buildingId"]],
        "apartments.parquet": apartments[["apartmentId", "rentalCost", "maxOccupancy", "numberOfRooms", "x", "y", "buildingId"]],
```

- [ ] **Step 5: Commit**

```bash
git add process_data.py
git commit -m "feat: add missing venue/building outputs to process_data.py"
```

---

### Task 3: Fix column name mismatches in `process_data.py`

**Files:**
- Modify: `process_data.py`

- [ ] **Step 1: Fix venue_checkins column name**

In the `process_checkin_journal()` function, change:
```python
        {"venueId": vid, "venueType": vt, "checkin_count": cnt}
```
to:
```python
        {"venueId": vid, "venueType": vt, "checkins": cnt}
```

- [ ] **Step 2: Fix travel_purpose_summary column names**

In the `process_travel_journal()` function, change:
```python
        {"purpose": p, "trip_count": cnt, "total_balance_change": round(purpose_cost.get(p, 0), 2)}
```
to:
```python
        {"purpose": p, "count": cnt, "total_spent": round(purpose_cost.get(p, 0), 2)}
```

- [ ] **Step 3: Fix participant_summary columns**

After the social degree enrichment section (before building outputs dict), add alias columns:

```python
    # Alias columns for app.py compatibility
    df_participant["avg_balance"] = df_participant["avg_availableBalance"]
    df_participant["social_degree"] = df_participant["total_social_interactions"]
```

- [ ] **Step 4: Fix job_summary to use employer-level data**

In the outputs dict, change `"job_summary.parquet"` to use `df_emp` instead of `df_jobs`, and rename the rate column:

```python
        "job_summary.parquet": df_emp.rename(columns={"avg_hourlyRate": "avg_hourly_rate"}),
```

- [ ] **Step 5: Commit**

```bash
git add process_data.py
git commit -m "fix: align column names with app.py expectations"
```

---

### Task 4: Update `app.py` to read `.parquet` instead of `.pkl`

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Change file extension in glob**

Line 33, change:
```python
for f in PROCESSED.glob("*.pkl"):
```
to:
```python
for f in PROCESSED.glob("*.parquet"):
```

- [ ] **Step 2: Change read method**

Line 35, change:
```python
data[key] = pd.read_pickle(f)
```
to:
```python
data[key] = pd.read_parquet(f)
```

- [ ] **Step 3: Fix `nlargest` usage for parquet compatibility**

Some older pandas/parquet versions don't preserve the `nlargest` method on all columns. Ensure venue_checkins uses correct sort. Line ~181, verify existing code uses correct column name `checkins`:

```python
top_venues = vc.nlargest(15, "checkins")
```

(This already matches after Task 3's rename.)

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "fix: switch app.py from .pkl to .parquet"
```

---

### Task 5: Run data processing and verify

**Files:**
- None (runtime verification)

- [ ] **Step 1: Install fastparquet if needed**

```bash
pip3 install fastparquet --quiet 2>&1 | tail -1
```

- [ ] **Step 2: Run process_data.py**

```bash
cd /mnt/d/homework/visulization/finalwork/VAST-Challenge-2022 && python3 process_data.py
```

Expected: All 5 steps complete, ~15 output files in `processed/`

- [ ] **Step 3: Verify output files exist with correct columns**

```bash
python3 -c "
import pandas as pd
from pathlib import Path
p = Path('processed')
for f in sorted(p.glob('*.parquet')):
    df = pd.read_parquet(f)
    print(f'{f.stem}: {len(df):,} rows, cols={list(df.columns[:8])}...')
"
```

- [ ] **Step 4: Quick smoke test of app.py**

```bash
cd /mnt/d/homework/visulization/finalwork/VAST-Challenge-2022 && streamlit run app.py --server.headless true &
sleep 5
curl -s http://localhost:8501 | head -20
pkill -f "streamlit run app.py"
```

- [ ] **Step 5: Commit processed directory to git (if not in .gitignore)**

```bash
git add processed/
git commit -m "data: add processed parquet files for MC1 dashboard"
```

---

### Task 6: Final verification and cleanup

- [ ] **Step 1: Full git status check**

```bash
git status
```

Expected: Clean working tree, all files committed.

- [ ] **Step 2: Review git log**

```bash
git log --oneline -10
```

- [ ] **Step 3: Ensure .gitignore covers large raw data**

```bash
cat .gitignore
```
Add `Datasets/` if not already ignored (raw data is too large for git).

