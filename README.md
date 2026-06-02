# VAST Challenge 2022 — Mini-Challenge 1: EngageTown

Visual analytics dashboard for the fictional city of EngageTown. Part of the [IEEE VAST Challenge 2022](https://vast-challenge.github.io/2022/).

## Quick Start

```bash
# 1. Process raw data (one-time, ~5-10 min)
python3 process_data.py

# 2. Launch dashboard
streamlit run app.py

# 3. Open browser → http://localhost:8501
```

**Prerequisites:** Python 3 +

```bash
pip install pandas fastparquet plotly streamlit networkx
```

## Repository Contents

### Tracked Files (in this repo)

```
.
├── app.py                  # Streamlit dashboard — 4-page visual analytics report
├── process_data.py         # Data pipeline: 114M rows → 14 parquet files
├── CLAUDE.md               # 🔧 Developer guide (architecture, data flow, TODOs, known issues)
├── README.md               # 📖 This file — project overview, challenge requirements, quick start
├── docs/
│   └── superpowers/
│       ├── specs/
│       │   └── 2026-05-30-mc1-improvement-plan.md  # 📋 Progress tracker & improvement roadmap
│       └── plans/
│           └── 2026-05-30-mc1-pipeline-fix.md      # Historical: pipeline bugfix plan
└── .gitignore              # Exclusion rules for large/data files
```

### NOT in This Repo (gitignored)

| Path | Reason | How to Obtain |
|------|--------|---------------|
| `Datasets/` | ~3GB raw CSV data | Download from [VAST Challenge 2022](https://vast-challenge.github.io/2022/) |
| `processed/` | Regeneratable parquet files | Run `python3 process_data.py` after placing Datasets/ |
| `BaseMap.png` | Large binary (455KB) | Included in official VAST data package |
| `Answer Sheets/` | Official submission templates | Included in official VAST data package |
| `VAST Challenge 2022 Dataset Descriptions.pdf` | Official PDF | Included in official VAST data package |
| `venv/` | Python virtual environment | Create locally with `python3 -m venv venv` |
| `.streamlit/` | Streamlit config | Auto-generated on first run |

> **To set up from scratch:** Download the VAST Challenge 2022 MC1 data package, place `Datasets/`, `Answer Sheets/`, `BaseMap.png`, and the PDF in the project root, then run `python3 process_data.py`.

## Documentation Guide

Where to look for what:

| What You Need | Read |
|---------------|------|
| What is this project? How do I run it? | `README.md` (this file) |
| How is the code structured? What's the data flow? | [`CLAUDE.md`](CLAUDE.md) |
| What's done? What's left to do? Priority order? | [`docs/superpowers/specs/2026-05-30-mc1-improvement-plan.md`](docs/superpowers/specs/2026-05-30-mc1-improvement-plan.md) |
| What was the original V1 state? | Improvement plan (gap analysis section) |
| How does the data pipeline work? | `CLAUDE.md` (data source mapping table) + `process_data.py` |

## Challenge Requirements (Official)

VAST Challenge 2022 Mini-Challenge 1 uses data from EngageTown, a fictional city. The data was collected from **1,011 volunteers** over **15 months** (March 2022 – May 2023), covering their activities, social interactions, finances, and travel.

### The Four Questions

**Q1 — Demographics** (≤10 images, ≤500 words)

> Assuming the volunteers are representative of the city's population, characterize what you can about the demographics of the town. Provide your rationale and supporting data.

**Q2 — Social Activities** (≤10 images, ≤500 words)

> Consider the social activities in the community. What patterns do you see in the social networks in the town? Describe up to ten significant patterns you observe, with evidence and rationale.

**Q3 — Business & Economy** (≤10 images, ≤500 words)

> Identify the predominant business base of the town. Describe patterns you identify.

**Q4 — Town Summary** (1 page)

> From your answers to questions 1-3, assemble a one-page summary that provides the key information to share with residents about the town.

### Dataset Description

| Dataset | Files | Records | Content |
|---------|-------|---------|---------|
| Activity Logs | 72 CSV | ~114M | Timestamped participant status (mode, hunger, sleep, balance, location) |
| Checkin Journal | 1 CSV | ~1.6M | Venue check-ins (venue ID, type) |
| Financial Journal | 1 CSV | ~1.4M | Financial transactions (category, amount) |
| Social Network | 1 CSV | ~3.7M | Social interactions between participant pairs |
| Travel Journal | 1 CSV | ~2.1M | Travel records (purpose, cost) |
| Attributes | 8 CSV | ~2.5K | Static info: participants, employers, jobs, buildings, pubs, restaurants, schools, apartments |

Full details in `VAST Challenge 2022 Dataset Descriptions.pdf` (from official data package).

### Submission Format

Final submission is an **Answer Sheet HTML file** (`index.htm`) containing:
- Team name, members, tools used, total hours
- Answers to all 4 questions with embedded images
- Link to a video demonstrating the visual analytics process

Template: `Answer Sheets/VAST Challenge 2022 C1 Answer Sheet.htm` (from official data package).

### Constraints

- Q1, Q2, Q3: each max **10 images** and **500 words**
- Q4: one-page summary
- All images must be referenced as relative links in the Answer Sheet
- Must report **tools used** and **total working hours**

---

## Key Findings

| Q | Question | Our Answer (Dashboard Page) |
|---|----------|---------------------------|
| Q1 | Characterize demographics | 1,011 residents, avg age 39, small households (2.0), 30% have kids, 10 evenly-distributed interest groups. 5 analysis findings with cross-referenced charts. |
| Q2 | 10 social patterns | Power-law degree distribution, 28 communities (modularity 0.52), tight-knit clusters, diurnal rhythm, bridge individuals, venue preferences, demographic correlations. Each pattern = chart + evidence block. |
| Q3 | Predominant business base | **253 micro-enterprises** (2-9 employees each) — a small-business service economy. No large corporations. Annual wages $55.6M. 5 economic findings. |
| Q4 | One-page summary | Three-column infographic: Who We Are / How We Live / Our Economy + venue map. |

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

## Data at a Glance

| Metric | Value |
|--------|-------|
| Residents | 1,011 |
| Average age | 39.1 |
| Household size | 2.0 |
| Kids | 29.8% |
| Interest groups | 10 (A-J, evenly distributed) |
| Social edges | 80,483 |
| Communities | 28 (modularity 0.52) |
| Annual wages | $55.6M |
| Employers | 253 (avg 5.2 employees, max 9) |
| Hourly wage | $10 – $41 (mean $19.22) |
| Buildings | 1,042 (526 residential / 512 commercial / 4 schools) |

## Current Status (V2, 2026-06-02)

**Done:**
- [x] Data pipeline processes all raw CSVs correctly
- [x] Dashboard upgraded from data browser to analysis report
- [x] Each finding includes chart + evidence text
- [x] Social network analysis (community detection, centrality, clustering)
- [x] Business base identified (small-business service economy)
- [x] Full documentation (README, CLAUDE.md, improvement plan)

**Still needed:**
- [ ] Generate Answer Sheet HTML for official submission
- [ ] Extract static chart images from plotly figures
- [ ] Write 500-word answers per question
- [ ] Q2 weekday-vs-weekend pattern analysis
- [ ] UI polish (color consistency, responsive layout)

More detail in [`CLAUDE.md`](CLAUDE.md) and [`docs/superpowers/specs/2026-05-30-mc1-improvement-plan.md`](docs/superpowers/specs/2026-05-30-mc1-improvement-plan.md).

## Key Technical Decisions

- **Network analysis in-memory** — graph metrics computed in `app.py` via `@st.cache_data`, not pre-processed. Keeps `process_data.py` simple. First load +10-30s.
- **Dynamic values** — all chart numbers are computed live from data, no hardcoded values.
- **Evidence blocks** — HTML callout boxes with `unsafe_allow_html=True` for analysis text.
- **No new dependencies beyond networkx** — all visualization with plotly and streamlit native components.

## References

- [VAST Challenge 2022 Official Site](https://vast-challenge.github.io/2022/)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Plotly Python](https://plotly.com/python/)
- [NetworkX Documentation](https://networkx.org)
