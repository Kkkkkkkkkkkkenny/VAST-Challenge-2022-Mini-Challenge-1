# VAST Challenge 2022 — Mini-Challenge 1: EngageTown

Visual analytics dashboard for the fictional city of EngageTown. Part of the [IEEE VAST Challenge 2022](https://vast-challenge.github.io/2022/).

## Overview

**Challenge:** Analyze EngageTown's data to answer 4 questions about its population, social networks, business economy, and produce a one-page town summary.

**Approach:** Streamlit dashboard with plotly visualizations + networkx graph analysis. Each question is answered with analysis findings backed by quantitative evidence.

## Quick Start

```bash
# 1. Process raw data (one-time, ~5-10 min)
python3 process_data.py

# 2. Launch dashboard
streamlit run app.py

# 3. Open browser → http://localhost:8501
```

**Prerequisites:** Python 3, plus packages in requirements:

```bash
pip install pandas fastparquet plotly streamlit networkx
```

## Project Structure

```
.
├── app.py                  # Streamlit dashboard (4-page analysis report)
├── process_data.py         # Data pipeline: 114M rows → 14 parquet files
├── CLAUDE.md               # Developer guide (architecture, state, TODOs)
├── README.md               # This file
├── BaseMap.png             # City map for venue overlay
├── Datasets/               # Raw CSVs (gitignored, ~3GB)
│   ├── Activity Logs/      # 72 participant status log files
│   ├── Journals/           # Checkin, Financial, Social, Travel
│   └── Attributes/         # Participants, Employers, Buildings, etc.
├── processed/              # Output parquet files (gitignored, regeneratable)
├── docs/
│   └── superpowers/specs/  # Improvement plan & design docs
└── Answer Sheets/          # Official MC1 submission templates
```

## The Four Questions

| Page | Question | Key Findings |
|------|----------|-------------|
| Q1 Demographics | Characterize the town's population | 1,011 residents, avg age 39, small households (2.0), 30% have kids, 10 evenly-distributed interest groups |
| Q2 Social Activities | Describe 10 patterns in social networks | Power-law degree distribution, 28 communities (modularity 0.52), tight-knit clusters, diurnal activity rhythm, bridge individuals |
| Q3 Business & Economy | Identify the predominant business base | **253 micro-enterprises** (2-9 employees each) — a small-business service economy. No large corporations. Balanced residential/commercial building mix. |
| Q4 Town Summary | One-page summary for residents | Infographic layout: population, social life, economy, map with venue markers |

## Data Pipeline

```
Datasets/                    process_data.py            processed/
─────────────────────────────────────────────────────────────────────
Activity Logs (72 files)  →  process_activity_logs() →  participant_summary
                                                         hourly_activity
                                                         daily_activity
Attributes/*.csv           →  load_attributes()       →  pubs, restaurants,
                                                         schools, apartments
CheckinJournal.csv         →  process_checkin_journal() → venue_checkins
FinancialJournal.csv       →  process_financial_journal() → financial_summary
                                                            daily_financial
SocialNetwork.csv          →  process_social_network()  → social_network
TravelJournal.csv          →  process_travel_journal()  → travel_purpose_summary
Jobs.csv + Employers.csv   →  build_job_summaries()     → job_summary
Buildings.csv              →  (value_counts)            → building_types
```

## Current Status (V2, 2026-06-02)

**Done:**
- [x] Data pipeline processes all raw CSVs correctly
- [x] Dashboard upgraded from data browser to analysis report
- [x] Each finding includes chart + evidence text
- [x] Social network analysis (community detection, centrality, clustering)
- [x] Business base identified (small-business service economy)

**Still needed:**
- [ ] Generate Answer Sheet HTML for official submission
- [ ] Extract static chart images from plotly figures
- [ ] Write 500-word answers per question
- [ ] Q2 weekday-vs-weekend pattern analysis
- [ ] UI polish (color consistency, responsive layout)

See `CLAUDE.md` and `docs/superpowers/specs/2026-05-30-mc1-improvement-plan.md` for full details.

## Key Technical Decisions

- **Network analysis runs in-memory in app.py** (via `@st.cache_data`), not pre-computed in process_data.py. This keeps the data pipeline simple. Recomputing on first page load takes ~10-30s.
- **All chart values are dynamic** — no hardcoded numbers. Changing the data and re-running `process_data.py` will update all visualizations.
- **HTML analysis blocks use `unsafe_allow_html=True`** for styled evidence boxes.

## Data at a Glance

| Metric | Value |
|--------|-------|
| Residents | 1,011 |
| Average age | 39.1 |
| Household size | 2.0 |
| Social edges | 80,483 |
| Communities | 28 (modularity 0.52) |
| Annual wages | $55.6M |
| Employers | 253 (avg 5.2 employees) |
| Hourly wage range | $10 – $41 |
| Buildings | 1,042 (526 residential / 512 commercial / 4 schools) |

## References

- [VAST Challenge 2022](https://vast-challenge.github.io/2022/)
- [MC1 Dataset Description](VAST%20Challenge%202022%20Dataset%20Descriptions.pdf)
- Streamlit: https://streamlit.io
- Plotly: https://plotly.com/python/
- NetworkX: https://networkx.org
