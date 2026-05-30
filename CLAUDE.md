# VAST Challenge 2022 MC1 — EngageTown Dashboard

## Project Goal
Complete Mini-Challenge 1: visual analytics of EngageTown fictional city data.
Answer 4 questions (demographics, social activities, business economy, town summary).
Final deliverable: analysis report with insights, not just data browsing.

## Key Files
- `app.py` — Streamlit dashboard (4 pages, reading parquet from processed/)
- `process_data.py` — Data pipeline: 114M activity logs + 13.5M journals → 14 parquet files
- `Datasets/` — Raw CSV data (gitignored, ~3GB, 72 activity files + 4 journals + 8 attributes)
- `processed/` — Output parquet files (gitignored, regeneratable via `python3 process_data.py`)

## Improvement Plan
See `docs/superpowers/specs/2026-05-30-mc1-improvement-plan.md`
Current V1 is a data browser; needs to become an analysis report.
6 phases: data enhancement → Q1-Q4 improvements → polish.

## Tech Stack
- Python 3, pandas, fastparquet, plotly, streamlit
- Run dashboard: `streamlit run app.py`
- Tailscale IP: 100.81.74.3

## Git
- Branch: master (main is upstream)
- Datasets/, processed/, venv/ are gitignored
