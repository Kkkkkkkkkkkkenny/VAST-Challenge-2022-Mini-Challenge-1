"""
common.py — Shared Analysis Engine for EngageTown MC1
======================================================
Single source of truth for data loading, network analysis, chart generation,
and utility functions shared between:

  - app.py (Streamlit interactive dashboard)
  - export_answer_sheet.py (Answer Sheet HTML generator)

Import from here instead of duplicating logic. Every function is
pure-Python — no Streamlit dependency — so both consumers can use them.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from pathlib import Path
import base64
from collections import Counter
from scipy import stats

# ═══════════════════════════════════════════════════════════════════════
# PATH CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_ROOT = SCRIPT_DIR  # project root = VAST-Challenge-2022/ (Datasets/ lives here)
PROCESSED = SCRIPT_DIR / "processed"
BASE = SCRIPT_DIR  # project root (BaseMap.png, etc.)

# ═══════════════════════════════════════════════════════════════════════
# COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════════

COLORS = px.colors.qualitative.Plotly
PALETTE = {
    "primary": "#2E4057",
    "secondary": "#4C78A8",
    "accent": "#F58518",
    "green": "#54A24B",
    "red": "#E45756",
    "purple": "#B279A2",
    "teal": "#72B7B2",
    "pink": "#FF9DA6",
}

# ═══════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════

def load_data():
    """Load all processed parquet files into a dict keyed by stem name."""
    data = {}
    for f in PROCESSED.glob("*.parquet"):
        key = f.stem
        data[key] = pd.read_parquet(f)
    return data


def load_base_map():
    """Read BaseMap.png -> base64 string, or None if missing."""
    map_path = BASE / "BaseMap.png"
    if map_path.exists():
        with open(map_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


# ═══════════════════════════════════════════════════════════════════════
# NETWORK ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def compute_network_metrics(social_df):
    """Compute social network graph metrics with networkx.

    Returns a dict with keys:
      degree, betweenness, clustering, communities (DataFrames),
      num_communities, modularity, num_nodes, num_edges,
      avg_clustering, density
    """
    G = nx.Graph()
    for _, row in social_df.iterrows():
        G.add_edge(row["participantIdFrom"], row["participantIdTo"], weight=row["weight"])

    metrics = {}

    # Degree
    degrees = dict(G.degree(weight="weight"))
    metrics["degree"] = pd.DataFrame(
        {"participantId": list(degrees.keys()), "weighted_degree": list(degrees.values())}
    )

    # Betweenness centrality (on largest component for performance)
    components = list(nx.connected_components(G))
    if not components:
        metrics["betweenness"] = pd.DataFrame(columns=["participantId", "betweenness_centrality"])
        metrics["clustering"] = pd.DataFrame(columns=["participantId", "clustering_coefficient"])
        metrics["communities"] = pd.DataFrame(columns=["participantId", "community"])
        metrics["num_communities"] = 0
        metrics["modularity"] = 0
        return metrics
    largest_cc = G.subgraph(max(components, key=len))
    betweenness = nx.betweenness_centrality(largest_cc, k=min(200, len(largest_cc)), weight="weight")
    metrics["betweenness"] = pd.DataFrame(
        {"participantId": list(betweenness.keys()), "betweenness_centrality": list(betweenness.values())}
    )

    # Clustering coefficient
    clustering = nx.clustering(G, weight="weight")
    metrics["clustering"] = pd.DataFrame(
        {"participantId": list(clustering.keys()), "clustering_coefficient": list(clustering.values())}
    )

    # Community detection (Louvain)
    try:
        communities = nx.community.louvain_communities(G, weight="weight")
        community_map = {}
        for i, comm in enumerate(communities):
            for node in comm:
                community_map[node] = i
        metrics["communities"] = pd.DataFrame(
            {"participantId": list(community_map.keys()), "community": list(community_map.values())}
        )
        metrics["num_communities"] = len(communities)
        metrics["modularity"] = nx.community.modularity(G, communities, weight="weight")
    except Exception:
        metrics["num_communities"] = 0
        metrics["modularity"] = 0

    # Graph-level stats
    metrics["num_nodes"] = G.number_of_nodes()
    metrics["num_edges"] = G.number_of_edges()
    metrics["avg_clustering"] = nx.average_clustering(G, weight="weight")
    metrics["density"] = nx.density(G)

    return metrics


# ═══════════════════════════════════════════════════════════════════════
# DATA PREPARATION
# ═══════════════════════════════════════════════════════════════════════

def prepare_cross_analysis(ps, net_metrics):
    """Cross-reference demographics with social activity metrics.

    Merges participant_summary with degree, betweenness, and clustering
    DataFrames from compute_network_metrics().  Fills missing values with 0.
    """
    df = ps[["participantId", "age", "educationLevel", "interestGroup",
              "householdSize", "haveKids", "joviality", "avg_balance"]].copy()

    if "degree" in net_metrics:
        df = df.merge(net_metrics["degree"], on="participantId", how="left")
    if "betweenness" in net_metrics:
        df = df.merge(net_metrics["betweenness"], on="participantId", how="left")
    if "clustering" in net_metrics:
        df = df.merge(net_metrics["clustering"], on="participantId", how="left")

    df["weighted_degree"] = df["weighted_degree"].fillna(0)
    df["betweenness_centrality"] = df["betweenness_centrality"].fillna(0)
    df["clustering_coefficient"] = df["clustering_coefficient"].fillna(0)
    return df


def prepare_hourly_activity(ha):
    """Add derived columns to hourly_activity DataFrame.

    Adds: total_mode, hour_num, dayofweek, is_weekend.
    Returns the mode column names list and the mutated DataFrame.
    """
    mode_cols = [c for c in ha.columns if c.startswith("mode_")]
    ha["total_mode"] = ha[mode_cols].sum(axis=1)
    ha["hour_num"] = pd.to_datetime(ha["hour"]).dt.hour
    ha["dayofweek"] = pd.to_datetime(ha["hour"]).dt.dayofweek
    ha["is_weekend"] = ha["dayofweek"].isin([5, 6])
    return mode_cols


def prepare_employer_industry(data, js):
    """Classify employers by industry using building co-location + education requirements.

    Classification hierarchy:
      1. Building co-location with known venues (pub/restaurant) - highest confidence
      2. Dominant education requirement from Jobs.csv - fills remaining employers:
         - Graduate          -> Professional Services
         - Bachelors         -> Business Services
         - HighSchoolOrCollege -> Retail & Services
         - Low               -> Basic Services

    Returns (js_with_ind, ind_counts, emp_bld) where js_with_ind is the
    job_summary DataFrame with an 'industry' column added.
    """
    emp_bld = pd.read_csv(DATA_ROOT / "Datasets" / "Attributes" / "Employers.csv")
    emp_bld = emp_bld[["employerId", "buildingId"]]

    # --- Step 1: venue co-location classification ---
    pubs_df = data.get("pubs", pd.DataFrame(columns=["buildingId"]))
    rest_df = data.get("restaurants", pd.DataFrame(columns=["buildingId"]))
    pub_bids = set(pubs_df["buildingId"]) if len(pubs_df) > 0 else set()
    rest_bids = set(rest_df["buildingId"]) if len(rest_df) > 0 else set()

    def assign_venue_industry(bid):
        in_pub = bid in pub_bids
        in_rest = bid in rest_bids
        if in_pub and in_rest:
            return "Food & Beverage"
        elif in_pub:
            return "Pub/Hospitality"
        elif in_rest:
            return "Restaurant/Food Service"
        return None

    emp_bld["industry"] = emp_bld["buildingId"].apply(assign_venue_industry)

    # --- Step 2: education-based classification for unclassified employers ---
    jobs_df = pd.read_csv(DATA_ROOT / "Datasets" / "Attributes" / "Jobs.csv")
    edu_to_industry = {
        "Graduate": "Professional Services",
        "Bachelors": "Business Services",
        "HighSchoolOrCollege": "Retail & Services",
        "Low": "Basic Services",
    }

    # Dominant education requirement per employer (most common among its jobs)
    emp_edu = (
        jobs_df.groupby("employerId")["educationRequirement"]
        .agg(lambda x: x.value_counts().index[0])
        .reset_index()
    )
    emp_edu.columns = ["employerId", "primary_edu_req"]
    emp_edu["edu_industry"] = emp_edu["primary_edu_req"].map(edu_to_industry)

    # Merge education info into emp_bld
    emp_bld = emp_bld.merge(
        emp_edu[["employerId", "edu_industry"]], on="employerId", how="left"
    )

    # Fill: use education-based industry for employers without venue co-location
    mask = emp_bld["industry"].isna()
    emp_bld.loc[mask, "industry"] = emp_bld.loc[mask, "edu_industry"]
    emp_bld.drop(columns=["edu_industry"], inplace=True)

    # --- Step 3: merge into job_summary ---
    js_with_ind = js.merge(emp_bld[["employerId", "industry"]], on="employerId", how="left")
    js_with_ind["industry"] = js_with_ind["industry"].fillna("Retail & Services")

    ind_counts = js_with_ind["industry"].value_counts()
    return js_with_ind, ind_counts, emp_bld


# ═══════════════════════════════════════════════════════════════════════
# DERIVED ECONOMIC METRICS
# ═══════════════════════════════════════════════════════════════════════

def compute_economic_metrics(fin, js, bt, ps):
    """Compute all derived economic metrics from financial/journal summaries.

    Returns a dict with keys like total_wage, total_shelter, total_food, etc.
    """
    total_wage = fin[fin["category"] == "Wage"]["total_amount"].sum()
    total_shelter = abs(fin[fin["category"] == "Shelter"]["total_amount"].sum())
    total_food = abs(fin[fin["category"] == "Food"]["total_amount"].sum())
    total_recreation = abs(fin[fin["category"] == "Recreation"]["total_amount"].sum())
    total_edu = abs(fin[fin["category"] == "Education"]["total_amount"].sum())
    total_spending = abs(fin[fin["category"] != "Wage"]["total_amount"].sum())
    total_jobs = js["employee_count"].sum()

    bt_dict = dict(zip(bt["buildingType"], bt["count"]))
    commercial = bt_dict.get("Commercial", 0)
    residential = bt_dict.get("Residental", 0)
    schools_n = bt_dict.get("School", 0)

    min_e = int(js["employee_count"].min())
    max_e = int(js["employee_count"].max())

    jobs_per_resident = total_jobs / len(ps)

    return {
        "total_wage": total_wage,
        "total_shelter": total_shelter,
        "total_food": total_food,
        "total_recreation": total_recreation,
        "total_edu": total_edu,
        "total_spending": total_spending,
        "total_jobs": total_jobs,
        "jobs_per_resident": jobs_per_resident,
        "bt_dict": bt_dict,
        "commercial": commercial,
        "residential": residential,
        "schools_n": schools_n,
        "min_e": min_e,
        "max_e": max_e,
    }


def compute_weekend_metrics(ha, mode_cols):
    """Compute weekday vs weekend activity metrics.

    Returns dict with we_work_pct, wd_work_pct, we_rec_pct, wd_rec_pct,
    we_peak, wd_peak.
    """
    we_mask = ha["is_weekend"]
    wd_mask = ~ha["is_weekend"]

    we_total = ha.loc[we_mask, mode_cols].sum().sum()
    wd_total = ha.loc[wd_mask, mode_cols].sum().sum()

    we_work_pct = 100 * ha.loc[we_mask, "mode_AtWork"].sum() / we_total if we_total > 0 else 0
    wd_work_pct = 100 * ha.loc[wd_mask, "mode_AtWork"].sum() / wd_total if wd_total > 0 else 0
    we_rec_pct = 100 * ha.loc[we_mask, "mode_AtRecreation"].sum() / we_total if we_total > 0 else 0
    wd_rec_pct = 100 * ha.loc[wd_mask, "mode_AtRecreation"].sum() / wd_total if wd_total > 0 else 0

    # Peak hours
    weekend_hourly = ha.groupby(["is_weekend", "hour_num"])["total_mode"].sum().reset_index()
    we_h = weekend_hourly[weekend_hourly["is_weekend"]]
    wd_h = weekend_hourly[~weekend_hourly["is_weekend"]]
    we_peak = int(we_h.loc[we_h["total_mode"].idxmax(), "hour_num"]) if len(we_h) > 0 else 0
    wd_peak = int(wd_h.loc[wd_h["total_mode"].idxmax(), "hour_num"]) if len(wd_h) > 0 else 0

    return {
        "we_work_pct": we_work_pct,
        "wd_work_pct": wd_work_pct,
        "we_rec_pct": we_rec_pct,
        "wd_rec_pct": wd_rec_pct,
        "we_peak": we_peak,
        "wd_peak": wd_peak,
    }


# ═══════════════════════════════════════════════════════════════════════
# Q1 CHART GENERATION
# ═══════════════════════════════════════════════════════════════════════

def make_q1_age_histogram(ps):
    """Age distribution histogram with mean/median lines."""
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=ps["age"], nbinsx=35, marker_color=PALETTE["secondary"], opacity=0.8,
        hovertemplate="Age: %{x}<br>Count: %{y}<extra></extra>"
    ))
    # Place mean at top, median at bottom to avoid overlap
    fig.add_vline(x=ps["age"].mean(), line_dash="dash", line_color=PALETTE["red"],
                  annotation_text=f"Mean: {ps['age'].mean():.1f}", annotation_position="top")
    fig.add_vline(x=ps["age"].median(), line_dash="dot", line_color=PALETTE["accent"],
                  annotation_text=f"Median: {ps['age'].median():.0f}", annotation_position="bottom",annotation_yshift=-20)
    fig.update_layout(
        title="Age Distribution", height=400,
        xaxis_title="Age", yaxis_title="Count", bargap=0.05, showlegend=False
    )
    return fig


def make_q1_age_pie(ps):
    """Age group composition pie chart."""
    age_bins = [0, 18, 30, 45, 60, 100]
    age_labels = ["0-17", "18-29", "30-44", "45-59", "60+"]
    ps_age = ps.copy()
    ps_age["age_group"] = pd.cut(ps_age["age"], bins=age_bins, labels=age_labels)
    age_dist = ps_age["age_group"].value_counts().sort_index()
    fig = px.pie(values=age_dist.values, names=age_dist.index,
                 title="Age Group Composition",
                 color_discrete_sequence=px.colors.sequential.Blues_r)
    fig.update_layout(height=400)
    return fig


def make_q1_education_bar(ps):
    """Education level distribution bar chart."""
    edu_order = ["Low", "HighSchoolOrCollege", "Bachelors", "Graduate"]
    edu_labels = ["Low", "High School\nor College", "Bachelors", "Graduate"]
    edu_counts = ps["educationLevel"].value_counts()
    edu_vals = [edu_counts.get(e, 0) for e in edu_order]
    fig = px.bar(x=edu_labels, y=edu_vals,
                 title="Education Level Distribution",
                 labels={"x": "Education Level", "y": "Count"},
                 color=edu_vals, color_continuous_scale="Blues", text=edu_vals)
    fig.update_layout(height=400, showlegend=False)
    return fig


def make_q1_edu_balance(ps):
    """Average balance by education level bar chart with error bars."""
    edu_balance = ps.groupby("educationLevel")["avg_balance"].agg(["mean", "std", "count"]).reset_index()
    edu_balance = edu_balance[edu_balance["count"] > 10]
    fig = px.bar(edu_balance, x="educationLevel", y="mean", error_y="std",
                 title="Average Balance by Education Level",
                 labels={"educationLevel": "Education Level", "mean": "Avg Balance ($)"},
                 color="mean", color_continuous_scale="Viridis",
                 text=edu_balance["mean"].round(0))
    fig.update_layout(height=400, showlegend=False)
    return fig


def make_q1_edu_age_cross(ps):
    """Education level vs age group cross-analysis stacked bar chart.

    Shows education level composition within each age group as percentages,
    with absolute counts in hover tooltips.
    """
    age_bins = [0, 18, 30, 45, 60, 100]
    age_labels = ["0-17", "18-29", "30-44", "45-59", "60+"]
    edu_order = ["Low", "HighSchoolOrCollege", "Bachelors", "Graduate"]
    edu_labels_map = {"Low": "Low", "HighSchoolOrCollege": "HS/College",
                      "Bachelors": "Bachelors", "Graduate": "Graduate"}

    ps_c = ps.copy()
    ps_c["age_group"] = pd.cut(ps_c["age"], bins=age_bins, labels=age_labels)
    ct = pd.crosstab(ps_c["age_group"], ps_c["educationLevel"])
    # Ensure all edu levels present
    for e in edu_order:
        if e not in ct.columns:
            ct[e] = 0
    ct = ct[edu_order]
    # Normalize to percentages per row
    ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100

    colors = [PALETTE["secondary"], PALETTE["accent"], PALETTE["green"], PALETTE["red"]]

    fig = go.Figure()
    for i, edu in enumerate(edu_order):
        label = edu_labels_map.get(edu, edu)
        fig.add_trace(go.Bar(
            x=ct.index.astype(str),
            y=ct_pct[edu].values,
            name=label,
            marker_color=colors[i % len(colors)],
            text=[f"{v:.0f}%" if v > 0 else "" for v in ct_pct[edu].values],
            textposition="inside",
            hovertemplate=(
                f"<b>{label}</b><br>Age: %{{x}}<br>"
                "Count: %{customdata}<br>Share: %{y:.1f}%<extra></extra>"
            ),
            customdata=ct[edu].values,
        ))

    fig.update_layout(
        barmode="stack",
        title="Education Level Composition by Age Group",
        xaxis_title="Age Group",
        yaxis_title="Percentage (%)",
        yaxis=dict(range=[0, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="center", x=0.5),
        height=420,
        margin=dict(l=50, r=20, t=60, b=50),
    )
    return fig


def make_q1_household_size(ps):
    """Household size distribution bar chart."""
    hh_counts = ps["householdSize"].value_counts().sort_index()
    fig = px.bar(x=hh_counts.index.astype(str), y=hh_counts.values,
                 title="Household Size Distribution",
                 labels={"x": "Household Size", "y": "Count"},
                 color=hh_counts.values, color_continuous_scale="Greens", text=hh_counts.values)
    fig.update_layout(height=400, showlegend=False)
    return fig


def make_q1_kids_pie(ps):
    """Families with children pie chart."""
    kids_data = ps["haveKids"].value_counts()
    fig = px.pie(values=kids_data.values, names=["No Kids", "Have Kids"],
                 title="Families with Children",
                 color_discrete_sequence=[PALETTE["teal"], PALETTE["accent"]])
    fig.update_layout(height=400)
    return fig


def make_q1_interest_groups(ps):
    """Interest group distribution bar chart."""
    interest_counts = ps["interestGroup"].value_counts().sort_index()
    fig = px.bar(x=interest_counts.index, y=interest_counts.values,
                 title="Interest Group Distribution",
                 labels={"x": "Interest Group", "y": "Count"},
                 color=interest_counts.values, color_continuous_scale="Reds", text=interest_counts.values)
    fig.update_layout(height=400, showlegend=False)
    return fig


def make_q1_balance_hist(ps):
    """Optimised average balance histogram with clear dividers and polished layout."""

    fig = px.histogram(
        ps,
        x="avg_balance",
        nbins=50,
        title="Average Available Balance Distribution",
        color_discrete_sequence=[PALETTE["accent"]],
        labels={"avg_balance": "Avg Balance ($)", "count": "Frequency"},
        template="plotly_white"
    )

    median_val = ps["avg_balance"].median()
    fig.add_vline(
        x=median_val,
        line_dash="dash",
        line_color=PALETTE["red"],
        line_width=2,
        annotation_text=f"Median: ${median_val:.0f}",
        annotation_position="top right",
        annotation_font_color=PALETTE["red"]
    )

    fig.update_traces(
        marker_line_color='white',
        marker_line_width=1.2,
        opacity=0.9,
        hovertemplate="<b>Balance Range</b>: %{x}<br><b>Count</b>: %{y}<extra></extra>"
    )

    fig.update_layout(
        height=450,
        bargap=0.04,
        title_font=dict(size=18, family="Arial", color="#2C3E50"),
        hovermode="x unified",
        margin=dict(l=60, r=40, t=60, b=50)
    )

    fig.update_xaxes(
        ticksuffix="",
        showgrid=True,
        gridcolor="#F0F3F4"
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#F0F3F4"
    )

    return fig

def make_q1_joviality_hist(ps):
    """Optimised Joviality distribution histogram."""

    fig = px.histogram(
        ps,
        x="joviality",
        nbins=40,
        title="Joviality Distribution",
        labels={"joviality": "Joviality Score", "count": "Frequency"},
        color_discrete_sequence=[PALETTE["purple"]],
        template="plotly_white"
    )

    mean_val = ps["joviality"].mean()
    median_val = ps["joviality"].median()

    fig.add_vline(
        x=mean_val,
        line_dash="dash",
        line_color="#E74C3C",
        line_width=2,
        annotation_text=f"Mean: {mean_val:.2f}",
        annotation_position="top right",
        annotation_font_color="#E74C3C"
    )

    fig.add_vline(
        x=median_val,
        line_dash="dot",
        line_color="#2ECC71",
        line_width=2,
        annotation_text=f"Median: {median_val:.2f}",
        annotation_position="top left",
        annotation_font_color="#2ECC71"
    )

    fig.update_layout(
        height=450,
        bargap=0.03,
        title_font=dict(size=18, family="Arial", color="#2C3E50"),
        hovermode="x unified",
        margin=dict(l=50, r=50, t=60, b=50)
    )

    fig.update_traces(
        marker_line_color='white',
        marker_line_width=0.5,
        opacity=0.85,
        hovertemplate="<b>Joviality Range</b>: %{x}<br><b>Count</b>: %{y}<extra></extra>"
    )

    return fig
# ═══════════════════════════════════════════════════════════════════════
# Q2 CHART GENERATION
# ═══════════════════════════════════════════════════════════════════════

def make_q2_degree_distribution(deg_df):
    """Weighted degree distribution log-log histogram.

    Uses manually computed log-spaced bins and filters zero-count bins
    so that all visible bars contain data -- avoids invisible bars on log-y scale.
    """
    deg_vals = deg_df[deg_df["weighted_degree"] > 0]["weighted_degree"]
    if len(deg_vals) == 0:
        fig = go.Figure()
        fig.update_layout(title="Weighted Degree Distribution (no data)", height=400)
        return fig

    # Log-spaced bins -- essential for power-law degree distributions
    bins = np.logspace(np.log10(deg_vals.min()), np.log10(deg_vals.max()), 30)
    hist_counts, bin_edges = np.histogram(deg_vals, bins=bins)

    # Geometric-mean bin centers look better on log scale
    bin_centers = np.sqrt(bin_edges[:-1] * bin_edges[1:])

    # Drop empty bins -- log_y cannot render zero-height bars
    mask = hist_counts > 0
    bin_centers = bin_centers[mask]
    hist_counts = hist_counts[mask]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=bin_centers, y=hist_counts,
        marker_color=PALETTE["secondary"], opacity=0.8,
        marker_line=dict(width=0),
    ))
    fig.update_layout(
        title="Weighted Degree Distribution (log-log)",
        xaxis_title="Weighted Degree", yaxis_title="Count",
        xaxis_type="log", yaxis_type="log",
        height=400,
    )
    return fig


def make_q2_rank_frequency(deg_df):
    """Degree rank-frequency scatter plot (log-log)."""
    deg_sorted = deg_df[deg_df["weighted_degree"] > 0]["weighted_degree"].sort_values(ascending=False).reset_index(drop=True)
    deg_sorted = deg_sorted[deg_sorted > 0]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(1, len(deg_sorted) + 1)), y=deg_sorted.values,
        mode="markers", marker=dict(color=PALETTE["accent"], size=3, opacity=0.6),
        name="Degree Rank"
    ))
    fig.update_layout(
        title="Degree Rank-Frequency (log-log)",
        xaxis_title="Rank", yaxis_title="Weighted Degree",
        xaxis_type="log", yaxis_type="log", height=400
    )
    return fig


def make_q2_community_sizes(net_metrics):
    """Community sizes bar chart."""
    if "communities" not in net_metrics or net_metrics["num_communities"] == 0:
        return None
    comm_df = net_metrics["communities"]
    comm_sizes = comm_df["community"].value_counts().sort_index()
    fig = px.bar(x=comm_sizes.index.astype(str), y=comm_sizes.values,
                 title=f"Community Sizes ({net_metrics['num_communities']} communities)",
                 labels={"x": "Community ID", "y": "Members"},
                 color=comm_sizes.values, color_continuous_scale="Viridis")
    fig.update_layout(height=400, showlegend=False)
    return fig


def make_q2_clustering_hist(net_metrics):
    """Clustering coefficient distribution histogram."""
    clust_df = net_metrics["clustering"]
    clust_nonzero = clust_df[clust_df["clustering_coefficient"] > 0]
    fig = px.histogram(clust_nonzero, x="clustering_coefficient", nbins=50,
                       title="Clustering Coefficient Distribution",
                       color_discrete_sequence=[PALETTE["purple"]],
                       labels={"clustering_coefficient": "Clustering Coefficient"})
    fig.update_layout(height=400)
    return fig


def make_q2_betweenness_hist(net_metrics):
    """Betweenness centrality distribution histogram."""
    btwn_df = net_metrics["betweenness"]
    btwn_nonzero = btwn_df[btwn_df["betweenness_centrality"] > 0]
    fig = px.histogram(btwn_nonzero, x="betweenness_centrality", nbins=50,
                       title="Betweenness Centrality Distribution",
                       color_discrete_sequence=[PALETTE["teal"]],
                       log_y=True,
                       labels={"betweenness_centrality": "Betweenness Centrality"})
    fig.update_layout(height=400)
    return fig


def make_q2_bridge_individuals(net_metrics):
    """Top 10 bridge individuals bar chart (horizontal)."""
    betweenness = net_metrics["betweenness"]
    top_bridge = betweenness.nlargest(10, "betweenness_centrality")
    fig = px.bar(top_bridge.sort_values("betweenness_centrality"),
                 x="betweenness_centrality", y="participantId",
                 orientation="h",
                 title="Top 10 Bridge Individuals (Betweenness Centrality)",
                 labels={"betweenness_centrality": "Betweenness Centrality",
                         "participantId": "Participant ID"},
                 color="betweenness_centrality", color_continuous_scale="Reds",
                 text=top_bridge["betweenness_centrality"].round(6))
    fig.update_layout(height=400, yaxis=dict(type="category"))
    return fig


def make_q2_venue_types(vc):
    """Venue type check-ins bar chart."""
    venue_type_counts = vc.groupby("venueType")["checkins"].sum().sort_values(ascending=False)
    fig = px.bar(x=venue_type_counts.index, y=venue_type_counts.values,
                 title="Total Check-ins by Venue Type",
                 labels={"x": "Venue Type", "y": "Total Check-ins"},
                 color=venue_type_counts.values, color_continuous_scale="Blues",
                 text=venue_type_counts.values)
    fig.update_layout(height=400, showlegend=False)
    return fig


def make_q2_top_venues(vc):
    """Top 10 most visited venues bar chart."""
    top_venues = vc.nlargest(10, "checkins")
    fig = px.bar(top_venues, x="venueId", y="checkins", color="venueType",
                 title="Top 10 Most Visited Venues",
                 color_discrete_sequence=COLORS)
    fig.update_layout(height=400, xaxis_tickangle=-45)
    return fig


def make_q2_hourly_activity(ha, mode_cols):
    """Activity modes by hour of day line chart (average across all days)."""
    mode_hourly = ha.groupby("hour_num")[mode_cols].mean()
    mode_hourly.columns = [c.replace("mode_", "") for c in mode_hourly.columns]
    fig = px.line(mode_hourly, title="Activity Modes by Hour of Day",
                  color_discrete_sequence=COLORS)
    fig.update_layout(height=400, xaxis_title="Hour", yaxis_title="Avg People",
                      legend=dict(orientation="h", y=1.1))
    return fig


def make_q2_mode_area(ha, mode_cols):
    """Activity modes throughout the day stacked area chart (average across all days)."""
    mode_hourly = ha.groupby("hour_num")[mode_cols].mean()
    mode_hourly.columns = [c.replace("mode_", "") for c in mode_hourly.columns]
    fig = px.area(mode_hourly, title="Average Activity Modes Throughout the Day",
                  color_discrete_sequence=COLORS)
    fig.update_layout(height=400, xaxis_title="Hour", yaxis_title="Avg Records",
                      legend=dict(orientation="h", y=1.1))
    return fig


def make_q2_weekday_weekend(ha, mode_cols):
    """Weekday vs weekend activity modes line chart (average across days)."""
    hourly_avg = ha.groupby(["is_weekend", "hour_num"])[mode_cols].mean().reset_index()
    hourly_avg["Day Type"] = hourly_avg["is_weekend"].map({False: "Weekday", True: "Weekend"})
    melted = hourly_avg.melt(id_vars=["is_weekend", "hour_num", "Day Type"],
                             value_vars=mode_cols, var_name="Mode", value_name="Avg People")
    melted["Mode"] = melted["Mode"].str.replace("mode_", "")
    melted["Group"] = melted["Day Type"] + " - " + melted["Mode"]
    fig = px.line(melted, x="hour_num", y="Avg People", color="Mode", line_dash="Day Type",
                  title="Activity Modes by Hour: Weekday vs Weekend",
                  labels={"hour_num": "Hour", "Avg People": "Avg People", "Mode": "", "Day Type": ""},
                  color_discrete_sequence=COLORS)
    fig.update_layout(height=400, legend=dict(orientation="h", y=1.1))
    return fig


def make_q2_weekday_weekend_modes(ha, mode_cols):
    """Activity mode composition weekday vs weekend grouped bar chart (average per hour)."""
    # Calculate average activity per hour for each mode, then aggregate weekday vs weekend
    hourly_avg = ha.groupby(["is_weekend", "hour_num"])[mode_cols].mean().reset_index()
    weekend_mode = hourly_avg.groupby("is_weekend")[mode_cols].mean()
    weekend_mode["Day Type"] = weekend_mode.index.map({False: "Weekday", True: "Weekend"})
    weekend_mode_melt = weekend_mode.melt(id_vars="Day Type", var_name="Mode", value_name="Avg Count")
    weekend_mode_melt["Mode"] = weekend_mode_melt["Mode"].str.replace("mode_", "")
    fig = px.bar(weekend_mode_melt, x="Mode", y="Avg Count", color="Day Type",
                 barmode="group",
                 title="Activity Mode Composition: Weekday vs Weekend (Avg per Hour)",
                 labels={"Avg Count": "Avg Activity Records per Hour", "Mode": "Activity Mode", "Day Type": ""},
                 color_discrete_sequence=[PALETTE["primary"], PALETTE["accent"]])
    fig.update_layout(height=400, legend=dict(orientation="h", y=1.05))
    return fig


def make_q2_age_social(cross):
    """Age vs social connectivity scatter with LOWESS trendline."""
    fig = px.scatter(cross, x="age", y="weighted_degree",
                     title="Age vs Social Connectivity",
                     labels={"age": "Age", "weighted_degree": "Weighted Degree"},
                     opacity=0.5, color_discrete_sequence=[PALETTE["secondary"]],
                     trendline="lowess")
    fig.update_layout(height=400)
    return fig


def make_q2_edu_social(cross):
    """Education level vs social connectivity bar chart."""
    edu_social = cross.groupby("educationLevel")["weighted_degree"].agg(["mean", "std"]).reset_index()
    fig = px.bar(edu_social, x="educationLevel", y="mean", error_y="std",
                 title="Education Level vs Social Connectivity",
                 labels={"educationLevel": "Education", "mean": "Avg Weighted Degree"},
                 color="mean", color_continuous_scale="Viridis")
    fig.update_layout(height=400, showlegend=False)
    return fig


def make_q2_edge_weights(sn):
    """Optimised edge weight distribution chart (semi-log coordinates, polished grid and color gradient)."""

    fig = px.histogram(
        sn,
        x="weight",
        nbins=50,
        title="Edge Weight Distribution (Interaction Frequency)",
        color_discrete_sequence=[PALETTE["accent"]],
        log_y=True,
        template="plotly_white",
        labels={"weight": "Edge Weight (interactions)", "count": "Frequency"}
    )

    fig.update_traces(
        marker_line_color='white',
        marker_line_width=1.0,
        opacity=0.9,
        hovertemplate="<b>Interaction Range</b>: %{x}<br><b>Count</b>: %{y}<extra></extra>"
    )

    fig.update_yaxes(
        tickvals=[1, 10, 100, 1000, 10000, 100000],
        ticktext=["1", "10", "100", "1k", "10k", "100k"],
        showgrid=True,
        gridcolor="#EBF5FB"
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#F2F4F4"
    )

    fig.update_layout(
        height=450,
        bargap=0.03,
        title_font=dict(size=18, family="Arial", color="#2C3E50"),
        hovermode="x unified",
        margin=dict(l=60, r=40, t=60, b=50)
    )

    return fig


def make_q2_travel_purpose(tp):
    """Travel by purpose bar chart (count)."""
    fig = px.bar(tp, x="purpose", y="count",
                 title="Travel by Purpose",
                 labels={"purpose": "Purpose", "count": "Number of Trips"},
                 color="count", color_continuous_scale="Blues",
                 text=tp["count"])
    fig.update_layout(height=400, showlegend=False, xaxis_tickangle=-30)
    return fig


def make_q2_travel_spending(tp):
    """Total spending by travel purpose bar chart."""
    fig = px.bar(tp, x="purpose", y="total_spent",
                 title="Total Spending by Travel Purpose",
                 labels={"purpose": "Purpose", "total_spent": "Total Spent ($)"},
                 color="total_spent", color_continuous_scale="Reds",
                 text=tp["total_spent"].round(0))
    fig.update_layout(height=400, showlegend=False, xaxis_tickangle=-30)
    return fig


# ═══════════════════════════════════════════════════════════════════════
# Q2 STATISTICAL TESTS
# ═══════════════════════════════════════════════════════════════════════

def compute_peak_hour_stats(ha, mode_cols):
    """Compute peak hour statistics with confidence intervals.

    Returns dict with peak_hour, ci_lower, ci_upper, peak_value, trough_hour.
    """
    # Calculate total activity per hour across all days
    hourly_total = ha.groupby("hour_num")["total_mode"].sum()

    # Find peak hour
    peak_hour = int(hourly_total.idxmax())
    peak_value = hourly_total.max()

    # Find trough hour
    trough_hour = int(hourly_total.idxmin())
    trough_value = hourly_total.min()

    # Bootstrap confidence interval for peak hour
    # Group by day and hour, then resample
    daily_hourly = ha.groupby(["dayofweek", "hour_num"])["total_mode"].sum().reset_index()

    # For each hour, compute mean and std across days
    hour_stats = daily_hourly.groupby("hour_num")["total_mode"].agg(["mean", "std", "count"])

    # 95% CI for peak hour using t-distribution
    peak_mean = hour_stats.loc[peak_hour, "mean"]
    peak_std = hour_stats.loc[peak_hour, "std"]
    peak_n = hour_stats.loc[peak_hour, "count"]

    if peak_n > 1:
        t_val = stats.t.ppf(0.975, df=peak_n - 1)
        ci_margin = t_val * peak_std / np.sqrt(peak_n)
        ci_lower = peak_mean - ci_margin
        ci_upper = peak_mean + ci_margin
    else:
        ci_lower = peak_mean
        ci_upper = peak_mean

    return {
        "peak_hour": peak_hour,
        "peak_value": peak_value,
        "trough_hour": trough_hour,
        "trough_value": trough_value,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "peak_mean": peak_mean,
    }


def compute_age_social_significance(cross):
    """Test statistical significance of age-social connectivity relationship.

    Returns dict with correlation, p_value, and LOWESS R².
    """
    # Filter out zero-degree nodes for meaningful analysis
    df = cross[cross["weighted_degree"] > 0].copy()

    if len(df) < 10:
        return {"correlation": 0, "p_value": 1, "r_squared": 0}

    # Spearman correlation (non-parametric, robust to outliers)
    corr, p_val = stats.spearmanr(df["age"], df["weighted_degree"])

    # Polynomial regression R² (test for non-linear relationship)
    # Fit quadratic: degree ~ age + age²
    age_poly = np.polyfit(df["age"], df["weighted_degree"], 2)
    predicted = np.polyval(age_poly, df["age"])
    ss_res = np.sum((df["weighted_degree"] - predicted) ** 2)
    ss_tot = np.sum((df["weighted_degree"] - df["weighted_degree"].mean()) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    return {
        "correlation": corr,
        "p_value": p_val,
        "r_squared": r_squared,
    }


def compute_community_modularity_test(G, communities):
    """Test if community structure is significant vs random.

    Returns dict with modularity, z_score, and significance.
    """
    mod = nx.community.modularity(G, communities, weight="weight")

    # Compare to random networks
    n_random = 100
    random_mods = []
    for _ in range(n_random):
        # Create random graph with same degree sequence
        G_random = nx.configuration_model([d for _, d in G.degree()])
        G_random = nx.Graph(G_random)  # Remove parallel edges
        G_random.remove_edges_from(nx.selfloop_edges(G_random))

        try:
            comms_random = nx.community.louvain_communities(G_random, weight="weight")
            mod_random = nx.community.modularity(G_random, comms_random, weight="weight")
            random_mods.append(mod_random)
        except Exception:
            continue

    if random_mods:
        z_score = (mod - np.mean(random_mods)) / np.std(random_mods) if np.std(random_mods) > 0 else 0
        significance = "significant" if z_score > 1.96 else "not significant"
    else:
        z_score = 0
        significance = "unable to test"

    return {
        "modularity": mod,
        "z_score": z_score,
        "significance": significance,
    }


# ═══════════════════════════════════════════════════════════════════════
# Q3 CHART GENERATION
# ═══════════════════════════════════════════════════════════════════════

def make_q3_employer_size(js):
    """Employer size distribution bar chart."""
    emp_size_dist = js["employee_count"].value_counts().sort_index()
    fig = px.bar(x=emp_size_dist.index.astype(str), y=emp_size_dist.values,
                 title=f"Employer Size Distribution ({len(js)} employers, avg {js['employee_count'].mean():.1f} employees)",
                 labels={"x": "Number of Employees", "y": "Number of Employers"},
                 color=emp_size_dist.values, color_continuous_scale="Blues",
                 text=emp_size_dist.values)
    fig.update_layout(height=400, showlegend=False)
    return fig


def make_q3_financial_flow(fin):
    """Financial flow horizontal bar chart."""
    fin_sorted = fin.copy().sort_values("total_amount", ascending=True)
    fig = px.bar(fin_sorted, y="category", x="total_amount",
                 title="Net Financial Flow by Category",
                 color="total_amount", color_continuous_scale="RdBu",
                 orientation="h",
                 text=fin_sorted["total_amount"].apply(lambda x: f"${x:,.0f}"))
    fig.add_vline(x=0, line_color="black")
    fig.update_layout(height=420)
    return fig


def make_q3_expense_pie(fin):
    """Expense breakdown pie chart."""
    expenses = fin[fin["total_amount"] < 0].copy()
    expenses["abs_amount"] = expenses["total_amount"].abs()
    fig = px.pie(values=expenses["abs_amount"], names=expenses["category"],
                 title="Expense Breakdown by Category",
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(height=420)
    return fig


def make_q3_wage_hist(js):
    """Hourly wage distribution histogram."""
    fig = px.histogram(
        js,
        x="avg_hourly_rate",
        nbins=35,
        title="Average Hourly Rate Distribution",
        labels={"avg_hourly_rate": "Hourly Rate ($)", "count": "Count"},
        color_discrete_sequence=[PALETTE["green"]],
        template="plotly_white"
    )

    mean_val = js["avg_hourly_rate"].mean()
    median_val = js["avg_hourly_rate"].median()

    fig.add_vline(
        x=mean_val,
        line_dash="dash",
        line_color=PALETTE["red"],
        line_width=2,
        annotation_text=f"Mean: ${mean_val:.2f}",
        annotation_position="top right",
        annotation_font_color=PALETTE["red"]
    )

    fig.add_vline(
        x=median_val,
        line_dash="dot",
        line_color=PALETTE["accent"],
        line_width=2,
        annotation_text=f"Median: ${median_val:.2f}",
        annotation_position="top left",
        annotation_font_color=PALETTE["accent"]
    )

    fig.update_layout(
        height=400,
        bargap=0.03,
        title_font=dict(size=18, family="Arial", color="#2C3E50"),
        margin=dict(l=50, r=50, t=60, b=50)
    )

    fig.update_traces(
        marker_line_color='white',
        marker_line_width=0.5,
        opacity=0.85
    )

    return fig

def make_q3_wage_box(js):
    """Wage distribution by employer size box plot."""
    js_plot = js.copy()
    js_plot["size_label"] = js_plot["employee_count"].apply(
        lambda x: "2-3 emp" if x <= 3 else ("4-6 emp" if x <= 6 else "7-9 emp"))
    fig = px.box(js_plot, x="size_label", y="avg_hourly_rate",
                 title="Wage Distribution by Employer Size",
                 color="size_label",
                 labels={"size_label": "Employer Size", "avg_hourly_rate": "Hourly Rate ($)"},
                 points="outliers")
    fig.update_layout(height=400, showlegend=False)
    return fig


def make_q3_building_types(bt):
    """Building types pie chart."""
    fig = px.pie(values=bt["count"], names=bt["buildingType"],
                 title=f"Building Types ({bt['count'].sum()} total)",
                 color_discrete_sequence=px.colors.qualitative.Set3)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(height=400)
    return fig


def make_q3_industry_pie(js_with_ind, js):
    """Industry classification pie chart."""
    ind_counts = js_with_ind["industry"].value_counts()
    fig = px.pie(values=ind_counts.values, names=ind_counts.index,
                 title=f"Employer Industry Classification ({len(js)} employers)",
                 color_discrete_sequence=[PALETTE["primary"], PALETTE["accent"], PALETTE["teal"],
                                          PALETTE["green"], PALETTE["purple"], PALETTE["pink"]])
    fig.update_traces(textposition="inside", textinfo="percent+label+value")
    fig.update_layout(height=400)
    return fig


def make_q3_industry_wage(js_with_ind):
    """Industry wage distribution box plot."""
    fig = px.box(js_with_ind, x="industry", y="avg_hourly_rate", color="industry",
                 title="Hourly Rate Distribution by Industry",
                 labels={"avg_hourly_rate": "Average Hourly Rate ($)", "industry": ""},
                 color_discrete_sequence=[PALETTE["primary"], PALETTE["accent"], PALETTE["teal"],
                                          PALETTE["green"], PALETTE["purple"], PALETTE["pink"]])
    fig.update_layout(height=400, showlegend=False)
    return fig


# ═══════════════════════════════════════════════════════════════════════
# Q4 CHART GENERATION
# ═══════════════════════════════════════════════════════════════════════

def make_q4_mini_age(ps):
    """Mini age group bar chart for town summary."""
    age_bins = [0, 18, 30, 45, 60, 100]
    age_labels = ["0-17", "18-29", "30-44", "45-59", "60+"]
    ps_m = ps.copy()
    ps_m["age_group"] = pd.cut(ps_m["age"], bins=age_bins, labels=age_labels)
    age_summary = ps_m["age_group"].value_counts().sort_index()
    fig = px.bar(x=age_summary.index, y=age_summary.values,
                 title="Age Distribution",
                 color_discrete_sequence=[PALETTE["secondary"]],
                 labels={"x": "", "y": ""})
    fig.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
    return fig


def make_q4_mini_venue(vc):
    """Mini venue type horizontal bar chart."""
    vt_mini = vc.groupby("venueType")["checkins"].sum().sort_values(ascending=True)
    fig = px.bar(x=vt_mini.values, y=vt_mini.index,
                 title="Check-ins by Venue Type",
                 color_discrete_sequence=[PALETTE["green"]],
                 labels={"x": "", "y": ""}, orientation="h")
    fig.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
    return fig


def make_q4_mini_financial(fin):
    """Mini expense breakdown pie chart."""
    fin_pie = fin[fin["category"] != "Wage"].copy()
    fig = px.pie(values=fin_pie["total_amount"].abs(), names=fin_pie["category"],
                 title="Expense Breakdown",
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0), showlegend=True,
                      legend=dict(font=dict(size=8)))
    return fig


def make_venue_map(base_map, data):
    """Create the EngageTown venue map with pub/restaurant/school markers.

    Args:
        base_map: base64-encoded PNG string, or None
        data: dict with optional 'pubs', 'restaurants', 'schools' DataFrames

    Returns:
        plotly Figure or None if base_map is None
    """
    if not base_map:
        return None

    fig = go.Figure()
    fig.add_layout_image(
        dict(source=f"data:image/png;base64,{base_map}",
             xref="x", yref="y", x=-5000, y=8000,
             sizex=10000, sizey=10000, sizing="stretch", layer="below")
    )

    if "pubs" in data:
        df_v = data["pubs"]
        fig.add_trace(go.Scatter(
            x=df_v["x"], y=df_v["y"], mode="markers",
            name="Pubs", marker=dict(color="#E45756", size=10, symbol="circle"),
            text="Pub " + df_v["pubId"].astype(str), hoverinfo="text"
        ))
    if "restaurants" in data:
        df_v = data["restaurants"]
        fig.add_trace(go.Scatter(
            x=df_v["x"], y=df_v["y"], mode="markers",
            name="Restaurants", marker=dict(color="#54A24B", size=10, symbol="triangle-up"),
            text="Restaurant " + df_v["restaurantId"].astype(str), hoverinfo="text"
        ))
    if "schools" in data:
        df_v = data["schools"]
        fig.add_trace(go.Scatter(
            x=df_v["x"], y=df_v["y"], mode="markers",
            name="Schools", marker=dict(color="#4C78A8", size=14, symbol="diamond"),
            text="School " + df_v["schoolId"].astype(str), hoverinfo="text"
        ))

    fig.update_layout(
        xaxis=dict(range=[-5000, 5000], showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(range=[0, 8000], showgrid=False, zeroline=False, showticklabels=False),
        height=550, margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        title="EngageTown Venue Map"
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════
# DAILY TIME-SERIES CHARTS (Phase 2)
# ═══════════════════════════════════════════════════════════════════════

def make_q2_daily_activity_trends(daily_activity, mode_cols):
    """
    Daily activity trends by mode -- 7-day rolling average line chart.
    """
    df = daily_activity.copy()
    df = df.sort_values("day")

    df["day_str"] = df["day"].astype(str)

    fig = go.Figure()
    mode_labels = {
        "mode_AtHome": "At Home", "mode_AtWork": "At Work",
        "mode_Transport": "Transport", "mode_AtRecreation": "Recreation",
        "mode_AtRestaurant": "Eating"
    }

    colors = [
        "#2C3E50",
        "#E74C3C",
        "#E67E22",
        "#2ECC71",
        "#9B59B6"
    ]

    for i, col in enumerate(mode_cols):
        if col in df.columns:
            smoothed = df[col].rolling(window=7, min_periods=1).mean()
            label = mode_labels.get(col, col.replace("mode_", ""))

            fig.add_trace(go.Scatter(
                x=df["day_str"],
                y=smoothed,
                mode="lines",
                name=label,
                line=dict(width=2.0, color=colors[i % len(colors)]),
                hovertemplate=f"<b>{label}</b><br>Day %{{x}}<br>Count: %{{y:.0f}}<extra></extra>"
            ))

    fig.update_layout(
        title="Daily Activity Trends by Mode (7-day rolling avg)",
        xaxis_title="Day",
        yaxis_title="Activity Count",
        height=450,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=60, r=30, t=80, b=50)
    )

    fig.update_xaxes(
        type="category",
        showgrid=True,
        gridcolor="#F2F4F4",
        nticks=20
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#F2F4F4"
    )

    return fig


def make_q3_daily_financial_timeseries(daily_financial):
    """Daily net financial flows -- line chart showing income vs expense cycles."""
    df = daily_financial.copy()
    # Separate income (Wage) and expenses
    df_wage = df[df["category"] == "Wage"].groupby("day")["total_amount"].sum().reset_index()
    df_wage = df_wage.sort_values("day")
    df_wage_smooth = df_wage["total_amount"].rolling(window=7, min_periods=1).mean()

    # Aggregate all expenses (negative amounts)
    df_exp = df[df["total_amount"] < 0].groupby("day")["total_amount"].sum().reset_index()
    df_exp = df_exp.sort_values("day")
    df_exp_smooth = df_exp["total_amount"].abs().rolling(window=7, min_periods=1).mean()

    # Net flow
    df_net = df.groupby("day")["total_amount"].sum().reset_index()
    df_net = df_net.sort_values("day")
    df_net_smooth = df_net["total_amount"].rolling(window=7, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_wage["day"], y=df_wage_smooth, mode="lines",
        name="Wage Income (7d avg)", line=dict(width=2, color="#54A24B")
    ))
    fig.add_trace(go.Scatter(
        x=df_exp["day"], y=df_exp_smooth, mode="lines",
        name="Total Expenses (7d avg)", line=dict(width=2, color="#E45756")
    ))
    fig.add_trace(go.Scatter(
        x=df_net["day"], y=df_net_smooth, mode="lines",
        name="Net Flow (7d avg)", line=dict(width=1.5, color="#4C78A8", dash="dash")
    ))
    fig.add_hline(y=0, line_color="gray", line_width=0.5)
    fig.update_layout(
        title="Daily Financial Flows (7-day rolling average)",
        xaxis_title="Day", yaxis_title="Amount ($)",
        height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=60, r=20, t=40, b=40)
    )
    return fig


def make_q2_hourly_density_animation(ha, mode_cols, output_path):
    """Create animated bar chart race of hourly activity density by mode.

    Generates 24 frames (one per hour of day) showing how activity across the
    5 modes evolves throughout the day, then combines them into an animated GIF.

    Args:
        ha: hourly_activity DataFrame
        mode_cols: list of mode column names
        output_path: Path where the .gif file should be saved

    Returns:
        Path to the saved GIF file.
    """
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image

    mode_labels = {
        "mode_AtHome": "At Home",
        "mode_AtWork": "At Work",
        "mode_Transport": "Transport",
        "mode_AtRecreation": "Recreation",
        "mode_AtRestaurant": "Eating",
    }
    colors = ["#4C78A8", "#E45756", "#F58518", "#54A24B", "#B279A2"]

    # Ensure derived columns exist
    ha_copy = ha.copy()
    if "hour_num" not in ha_copy.columns:
        ha_copy["hour_num"] = pd.to_datetime(ha_copy["hour"]).dt.hour
    if "total_mode" not in ha_copy.columns:
        ha_copy["total_mode"] = ha_copy[mode_cols].sum(axis=1)

    # Aggregate mean activity per hour of day per mode
    hourly_avg = ha_copy.groupby("hour_num")[mode_cols].mean()
    max_val = hourly_avg.max().max() * 1.15

    frames = []
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=120)
    plt.style.use("ggplot")

    for hour in range(24):
        ax.clear()
        row = hourly_avg.loc[hour]
        labels = [mode_labels.get(c, c.replace("mode_", "")) for c in mode_cols]
        values = [row[c] for c in mode_cols]

        bars = ax.bar(labels, values, color=colors, edgecolor="white", linewidth=0.5)
        ax.set_ylim(0, max_val)
        ax.set_ylabel("Avg Activity Records", fontsize=10)
        ax.set_title(f"Activity Density by Mode -- {hour:02d}:00", fontsize=13, fontweight="bold")

        # Value labels above bars
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height() + max_val * 0.01,
                    f"{val:.0f}",
                    ha="center", va="bottom", fontsize=8, color="#333",
                )

        ax.tick_params(axis="x", labelsize=9)
        ax.tick_params(axis="y", labelsize=8)

        # Capture frame
        buf = io.BytesIO()
        fig.tight_layout(pad=1.5)
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="white")
        buf.seek(0)
        img = Image.open(buf)
        frames.append(img.copy())
        buf.close()

    plt.close(fig)

    # Save animated GIF
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=600,  # 600ms per frame
        loop=0,         # loop forever
    )
    return output_path
