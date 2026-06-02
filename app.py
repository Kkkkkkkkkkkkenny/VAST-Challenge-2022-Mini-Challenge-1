"""
VAST Challenge 2022 MC1 — EngageTown Visual Analytics Report
============================================================
从数据浏览器升级为分析报告：每个问题 = 分析结论 + 证据图表 + 数据支撑
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
from pathlib import Path
import base64
from collections import Counter

st.set_page_config(
    page_title="EngageTown Report | VAST 2022 MC1",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE = Path("/mnt/d/homework/visulization/finalwork/VAST-Challenge-2022")
PROCESSED = BASE / "processed"

# ============================================================
# Cache data loading
# ============================================================
@st.cache_data
def load_data():
    data = {}
    for f in PROCESSED.glob("*.parquet"):
        key = f.stem
        data[key] = pd.read_parquet(f)
    return data

@st.cache_data
def load_base_map():
    map_path = BASE / "BaseMap.png"
    if map_path.exists():
        with open(map_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

@st.cache_data
def compute_network_metrics(_social_df):
    """Compute social network graph metrics with networkx."""
    G = nx.Graph()
    for _, row in _social_df.iterrows():
        G.add_edge(row["participantIdFrom"], row["participantIdTo"], weight=row["weight"])

    metrics = {}

    # Degree
    degrees = dict(G.degree(weight="weight"))
    metrics["degree"] = pd.DataFrame(
        {"participantId": list(degrees.keys()), "weighted_degree": list(degrees.values())}
    )

    # Betweenness centrality (on largest component for performance)
    largest_cc = G.subgraph(max(nx.connected_components(G), key=len))
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

@st.cache_data
def compute_cross_analysis(ps, net_metrics):
    """Cross-reference demographics with social activity."""
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

# ============================================================
# Sidebar
# ============================================================
st.sidebar.title("🏙️ EngageTown")
st.sidebar.markdown("**VAST Challenge 2022 — Mini-Challenge 1**")
st.sidebar.markdown("Visual Analytics Report")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Q1: Demographics",
     "🤝 Q2: Social Activities",
     "🏭 Q3: Business & Economy",
     "📋 Q4: Town Summary"]
)

st.sidebar.markdown("---")
st.sidebar.caption("Data: VAST Challenge 2022 MC1")
st.sidebar.caption("Tools: Python, Streamlit, Plotly, NetworkX")

# ============================================================
# Load data
# ============================================================
try:
    data = load_data()
    base_map = load_base_map()
    data_loaded = True
except Exception as e:
    st.error(f"Data not processed. Run process_data.py first.\n\nError: {e}")
    data_loaded = False

if not data_loaded:
    st.stop()

# ============================================================
# Pre-compute network metrics & cross analysis
# ============================================================
ps = data["participant_summary"]
sn = data["social_network"]
vc = data["venue_checkins"]
fin = data["financial_summary"]
js = data["job_summary"]
ha = data["hourly_activity"]
tp = data["travel_purpose_summary"]
bt = data["building_types"]

# Color palette
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

@st.cache_data
def get_network_metrics(_sn):
    return compute_network_metrics(_sn)

@st.cache_data
def get_cross_analysis(_ps, _net_metrics):
    return compute_cross_analysis(_ps, _net_metrics)

net_metrics = get_network_metrics(sn)
cross = get_cross_analysis(ps, net_metrics)


# ============================================================
# Q1: Demographics
# ============================================================
if page.startswith("📊"):
    st.title("Q1: Town Demographics")
    st.markdown("*Assuming the volunteers are representative of the town's population, characterize the demographics.*")

    # --- Hero metrics ---
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Population", f"{len(ps):,}")
    with col2:
        st.metric("Avg Age", f"{ps['age'].mean():.1f}")
    with col3:
        st.metric("Median Age", f"{ps['age'].median():.0f}")
    with col4:
        st.metric("Avg Household", f"{ps['householdSize'].mean():.1f}")
    with col5:
        st.metric("Families w/ Kids", f"{ps['haveKids'].eq(True).mean()*100:.1f}%")
    with col6:
        st.metric("Interest Groups", f"{ps['interestGroup'].nunique()}")

    st.markdown("---")

    # --- Finding 1: Age Structure ---
    st.subheader("Finding 1: Age Structure — Predominantly Working-Age Adults")

    col_l, col_r = st.columns([2, 1])
    with col_l:
        fig_age = go.Figure()
        fig_age.add_trace(go.Histogram(
            x=ps["age"], nbinsx=35, name="Age",
            marker_color=PALETTE["secondary"], opacity=0.8,
            hovertemplate="Age: %{x}<br>Count: %{y}<extra></extra>"
        ))
        # Add mean/median lines
        for val, color, label in [(ps["age"].mean(), PALETTE["red"], f"Mean: {ps['age'].mean():.1f}"),
                                    (ps["age"].median(), PALETTE["accent"], f"Median: {ps['age'].median():.0f}")]:
            fig_age.add_vline(x=val, line_dash="dash", line_color=color,
                              annotation_text=label, annotation_position="top")
        fig_age.update_layout(
            title="Age Distribution with Mean & Median", height=400,
            xaxis_title="Age", yaxis_title="Count", bargap=0.05,
            showlegend=False
        )
        st.plotly_chart(fig_age, use_container_width=True)

    with col_r:
        age_bins = [0, 18, 30, 45, 60, 100]
        age_labels = ["0-17", "18-29", "30-44", "45-59", "60+"]
        ps_age = ps.copy()
        ps_age["age_group"] = pd.cut(ps_age["age"], bins=age_bins, labels=age_labels)
        age_dist = ps_age["age_group"].value_counts().sort_index()
        fig_pie = px.pie(values=age_dist.values, names=age_dist.index,
                         title="Age Group Composition",
                         color_discrete_sequence=px.colors.sequential.Blues_r)
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #4C78A8;">
    <strong>Analysis:</strong> The population is dominated by working-age adults (18–59), with a mean age of ~39.
    The distribution shows a slight right skew — fewer elderly residents. This suggests EngageTown is
    an economically active community with a relatively young workforce.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # --- Finding 2: Education & Income ---
    st.subheader("Finding 2: Education Level Correlates with Economic Status")

    col_l, col_r = st.columns(2)

    with col_l:
        edu_order = ["Low", "HighSchoolOrCollege", "Bachelors", "Graduate"]
        edu_labels = ["Low", "High School\nor College", "Bachelors", "Graduate"]
        edu_counts = ps["educationLevel"].value_counts()
        # Reorder
        edu_vals = [edu_counts.get(e, 0) for e in edu_order]
        fig_edu = px.bar(x=edu_labels, y=edu_vals,
                         title="Education Level Distribution",
                         labels={"x": "Education Level", "y": "Count"},
                         color=edu_vals, color_continuous_scale="Blues",
                         text=edu_vals)
        fig_edu.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_edu, use_container_width=True)

    with col_r:
        # Education vs Balance
        edu_balance = ps.groupby("educationLevel")["avg_balance"].agg(["mean", "std", "count"]).reset_index()
        edu_balance = edu_balance[edu_balance["count"] > 10]
        fig_eb = px.bar(edu_balance, x="educationLevel", y="mean",
                        error_y="std",
                        title="Average Balance by Education Level",
                        labels={"educationLevel": "Education Level", "mean": "Avg Balance ($)"},
                        color="mean", color_continuous_scale="Viridis",
                        text=edu_balance["mean"].round(0))
        fig_eb.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_eb, use_container_width=True)

    st.markdown("""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #4C78A8;">
    <strong>Analysis:</strong> The majority of residents have "High School or College" or "Bachelors" level education.
    Higher education correlates with higher average available balance, suggesting a link between education and
    economic well-being in EngageTown.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # --- Finding 3: Household & Family Structure ---
    st.subheader("Finding 3: Small Households, Mixed Family Structure")

    col_l, col_r = st.columns(2)

    with col_l:
        hh_counts = ps["householdSize"].value_counts().sort_index()
        fig_hh = px.bar(x=hh_counts.index.astype(str), y=hh_counts.values,
                        title="Household Size Distribution",
                        labels={"x": "Household Size", "y": "Count"},
                        color=hh_counts.values, color_continuous_scale="Greens",
                        text=hh_counts.values)
        fig_hh.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_hh, use_container_width=True)

    with col_r:
        kids_data = ps["haveKids"].value_counts()
        fig_kids = px.pie(values=kids_data.values, names=["No Kids", "Have Kids"],
                          title="Families with Children",
                          color_discrete_sequence=[PALETTE["teal"], PALETTE["accent"]])
        fig_kids.update_layout(height=400)
        st.plotly_chart(fig_kids, use_container_width=True)

    st.markdown("""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #54A24B;">
    <strong>Analysis:</strong> Average household size is exactly 2.0 — most households have just 2 members.
    About 30% of residents have children. Combined, this suggests many two-adult households
    without children, alongside smaller numbers of families with kids.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # --- Finding 4: Interest Groups & Social Diversity ---
    st.subheader("Finding 4: Even Distribution Across Interest Groups")

    interest_counts = ps["interestGroup"].value_counts().sort_index()
    fig_int = px.bar(x=interest_counts.index, y=interest_counts.values,
                     title="Interest Group Distribution",
                     labels={"x": "Interest Group", "y": "Count"},
                     color=interest_counts.values, color_continuous_scale="Reds",
                     text=interest_counts.values)
    fig_int.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_int, use_container_width=True)

    st.markdown("""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #E45756;">
    <strong>Analysis:</strong> The 10 interest groups (A–J) are remarkably evenly distributed (~100 members each).
    This suggests deliberate community design or self-organization, ensuring diverse social mixing rather
    than concentration in a few dominant interest areas.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # --- Finding 5: Economic Overview ---
    st.subheader("Finding 5: Financial Well-being")

    col_l, col_r = st.columns(2)

    with col_l:
        fig_bal = px.histogram(ps, x="avg_balance", nbins=50,
                               title="Average Available Balance Distribution",
                               color_discrete_sequence=[PALETTE["accent"]],
                               labels={"avg_balance": "Avg Balance ($)"})
        fig_bal.add_vline(x=ps["avg_balance"].median(), line_dash="dash", line_color=PALETTE["red"],
                          annotation_text=f"Median: ${ps['avg_balance'].median():.0f}")
        fig_bal.update_layout(height=400)
        st.plotly_chart(fig_bal, use_container_width=True)

    with col_r:
        # Joviality
        fig_joy = px.histogram(ps, x="joviality", nbins=40,
                               title="Joviality Distribution",
                               color_discrete_sequence=[PALETTE["purple"]])
        fig_joy.update_layout(height=400)
        st.plotly_chart(fig_joy, use_container_width=True)

    st.markdown("""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #F58518;">
    <strong>Analysis:</strong> The balance distribution is right-skewed — most residents have moderate balances
    with a long tail of higher-wealth individuals. Joviality (happiness metric) is roughly normally
    distributed around 0.5, suggesting a generally content population.
    </div>
    """, unsafe_allow_html=True)

    # --- Q1 Summary ---
    st.markdown("---")
    st.subheader("Q1 Summary: Who Lives in EngageTown?")
    st.markdown(f"""
    EngageTown is home to **{len(ps):,} residents** with a mean age of **{ps['age'].mean():.1f} years**,
    predominantly working-age adults (18-59). Households are small (avg {ps['householdSize'].mean():.1f} persons),
    with about **{ps['haveKids'].eq(True).mean()*100:.0f}%** having children.

    Education levels concentrate at "High School or College" and "Bachelors" — higher education correlates
    with better financial standing. The **{ps['interestGroup'].nunique()} interest groups** show remarkably
    even distribution, suggesting deliberate community design.

    Financially, most residents maintain moderate balances with a right-skewed distribution, and the
    population is generally content (joviality centered around 0.5).

    **Key takeaway:** EngageTown is a young, educated, small-family community with balanced social diversity
    and moderate economic well-being.
    """)


# ============================================================
# Q2: Social Activities
# ============================================================
elif page.startswith("🤝"):
    st.title("Q2: Social Activities & Networks")
    st.markdown("*What patterns do you see in the social networks? Describe up to 10 significant patterns with evidence.*")

    # --- Network overview metrics ---
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Nodes", f"{net_metrics['num_nodes']:,}")
    with col2:
        st.metric("Edges", f"{net_metrics['num_edges']:,}")
    with col3:
        st.metric("Network Density", f"{net_metrics['density']:.4f}")
    with col4:
        st.metric("Avg Clustering", f"{net_metrics['avg_clustering']:.4f}")
    with col5:
        st.metric("Communities", f"{net_metrics.get('num_communities', 'N/A')}")

    st.markdown("---")

    # Pattern 1: Degree Distribution
    st.subheader("Pattern 1: Heavy-Tailed Degree Distribution (Power Law)")

    deg_df = net_metrics["degree"]
    deg_df_nonzero = deg_df[deg_df["weighted_degree"] > 0]

    col_l, col_r = st.columns(2)
    with col_l:
        fig_d1 = px.histogram(deg_df_nonzero, x="weighted_degree", nbins=60,
                              title="Weighted Degree Distribution (log-log)",
                              color_discrete_sequence=[PALETTE["secondary"]],
                              log_x=True, log_y=True,
                              labels={"weighted_degree": "Weighted Degree"})
        fig_d1.update_layout(height=400)
        st.plotly_chart(fig_d1, use_container_width=True)

    with col_r:
        # Rank-frequency plot
        deg_sorted = deg_df_nonzero["weighted_degree"].sort_values(ascending=False).reset_index(drop=True)
        deg_sorted = deg_sorted[deg_sorted > 0]
        fig_rf = go.Figure()
        fig_rf.add_trace(go.Scatter(
            x=list(range(1, len(deg_sorted) + 1)), y=deg_sorted.values,
            mode="markers", marker=dict(color=PALETTE["accent"], size=3, opacity=0.6),
            name="Degree Rank"
        ))
        fig_rf.update_layout(
            title="Degree Rank-Frequency (log-log)",
            xaxis_title="Rank", yaxis_title="Weighted Degree",
            xaxis_type="log", yaxis_type="log", height=400
        )
        st.plotly_chart(fig_rf, use_container_width=True)

    top_degree = deg_df_nonzero.nlargest(5, "weighted_degree")
    st.markdown(f"""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #4C78A8;">
    <strong>Evidence:</strong> The degree distribution follows a heavy-tailed (near power-law) pattern on log-log
    scale — few individuals have very high social connectivity while most have moderate connections.
    Top 5 most connected: IDs {', '.join(map(str, top_degree['participantId'].tolist()))}.
    This is characteristic of real social networks.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Pattern 2: Community Structure
    st.subheader("Pattern 2: Strong Community Structure")
    st.markdown(f"Modularity: **{net_metrics.get('modularity', 0):.4f}** | Communities detected: **{net_metrics.get('num_communities', 'N/A')}**")

    if "communities" in net_metrics and net_metrics["num_communities"] > 0:
        comm_df = net_metrics["communities"]
        comm_sizes = comm_df["community"].value_counts().sort_index()
        fig_comm = px.bar(x=comm_sizes.index.astype(str), y=comm_sizes.values,
                          title=f"Community Sizes ({net_metrics['num_communities']} communities)",
                          labels={"x": "Community ID", "y": "Members"},
                          color=comm_sizes.values, color_continuous_scale="Viridis")
        fig_comm.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_comm, use_container_width=True)

    st.markdown("""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #54A24B;">
    <strong>Evidence:</strong> Louvain community detection reveals distinct social clusters. The high modularity
    score indicates well-separated communities — residents tend to interact more within their group than
    across groups. This may correspond to interest groups, neighborhoods, or workplace social circles.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Pattern 3: Clustering
    st.subheader("Pattern 3: High Local Clustering — Tight-Knit Friend Groups")

    clust_df = net_metrics["clustering"]
    clust_nonzero = clust_df[clust_df["clustering_coefficient"] > 0]

    col_l, col_r = st.columns(2)
    with col_l:
        fig_cl = px.histogram(clust_nonzero, x="clustering_coefficient", nbins=50,
                              title="Clustering Coefficient Distribution",
                              color_discrete_sequence=[PALETTE["purple"]],
                              labels={"clustering_coefficient": "Clustering Coefficient"})
        fig_cl.update_layout(height=400)
        st.plotly_chart(fig_cl, use_container_width=True)

    with col_r:
        # Betweenness
        btwn_df = net_metrics["betweenness"]
        btwn_nonzero = btwn_df[btwn_df["betweenness_centrality"] > 0]
        fig_bt = px.histogram(btwn_nonzero, x="betweenness_centrality", nbins=50,
                              title="Betweenness Centrality Distribution",
                              color_discrete_sequence=[PALETTE["teal"]],
                              log_y=True,
                              labels={"betweenness_centrality": "Betweenness Centrality"})
        fig_bt.update_layout(height=400)
        st.plotly_chart(fig_bt, use_container_width=True)

    avg_clust = clust_df["clustering_coefficient"].mean()
    st.markdown(f"""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #B279A2;">
    <strong>Evidence:</strong> Average clustering coefficient is {avg_clust:.4f} — significantly higher than
    the network density ({net_metrics['density']:.4f}). This "friends-of-friends-are-friends" pattern confirms
    tight-knit social circles. Betweenness centrality shows a few key individuals bridging communities.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Pattern 4: Venue Check-in Patterns
    st.subheader("Pattern 4: Venue Type Preference — Eating & Recreation Dominate")

    col_l, col_r = st.columns(2)
    with col_l:
        venue_type_counts = vc.groupby("venueType")["checkins"].sum().sort_values(ascending=False)
        fig_vt = px.bar(x=venue_type_counts.index, y=venue_type_counts.values,
                        title="Total Check-ins by Venue Type",
                        labels={"x": "Venue Type", "y": "Total Check-ins"},
                        color=venue_type_counts.values, color_continuous_scale="Blues",
                        text=venue_type_counts.values)
        fig_vt.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_vt, use_container_width=True)

    with col_r:
        top_venues = vc.nlargest(10, "checkins")
        fig_tv = px.bar(top_venues, x="venueId", y="checkins", color="venueType",
                        title="Top 10 Most Visited Venues",
                        color_discrete_sequence=COLORS)
        fig_tv.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_tv, use_container_width=True)

    top_type = venue_type_counts.index[0]
    st.markdown(f"""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #F58518;">
    <strong>Evidence:</strong> "{top_type}" venues dominate check-in activity, followed by other venue types.
    This suggests residents primarily use venues for social eating/drinking rather than other activities.
    The top venue concentration indicates a few highly popular gathering places.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Pattern 5: Temporal Activity Patterns
    st.subheader("Pattern 5: Diurnal Rhythm — Peak Social Activity in Afternoon/Evening")

    # Aggregate mode counts by hour
    mode_cols = [c for c in ha.columns if c.startswith("mode_")]
    ha["total_mode"] = ha[mode_cols].sum(axis=1)
    ha["hour_num"] = pd.to_datetime(ha["hour"]).dt.hour

    hourly_total = ha.groupby("hour_num")["total_mode"].sum().reset_index()

    fig_temp = px.bar(hourly_total, x="hour_num", y="total_mode",
                      title="Activity by Hour of Day",
                      labels={"hour_num": "Hour", "total_mode": "Activity Records"},
                      color="total_mode", color_continuous_scale="Viridis")
    fig_temp.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_temp, use_container_width=True)

    # Mode breakdown
    mode_hourly = ha.groupby("hour_num")[mode_cols].sum()
    fig_modes = px.area(mode_hourly, title="Activity Modes Throughout the Day",
                        color_discrete_sequence=COLORS)
    fig_modes.update_layout(height=400, xaxis_title="Hour", yaxis_title="Records",
                            legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_modes, use_container_width=True)

    peak_hour = hourly_total.loc[hourly_total["total_mode"].idxmax(), "hour_num"]
    st.markdown(f"""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #72B7B2;">
    <strong>Evidence:</strong> Activity peaks at hour {int(peak_hour)}:00. Clear diurnal pattern visible —
    low activity at night (sleeping), rising in morning (work), peaking in afternoon/evening (social).
    "AtHome" and "AtWork" modes dominate daytime while "Recreation" and "Eating" peak in evening.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Pattern 6: Social Connectivity vs Demographics
    st.subheader("Pattern 6: Age and Social Connectivity")

    col_l, col_r = st.columns(2)
    with col_l:
        fig_age_deg = px.scatter(cross, x="age", y="weighted_degree",
                                 title="Age vs Social Connectivity",
                                 labels={"age": "Age", "weighted_degree": "Weighted Degree"},
                                 opacity=0.5, color_discrete_sequence=[PALETTE["secondary"]],
                                 trendline="lowess")
        fig_age_deg.update_layout(height=400)
        st.plotly_chart(fig_age_deg, use_container_width=True)

    with col_r:
        # Education vs social
        edu_social = cross.groupby("educationLevel")["weighted_degree"].agg(["mean", "std"]).reset_index()
        fig_edu_soc = px.bar(edu_social, x="educationLevel", y="mean", error_y="std",
                             title="Education Level vs Social Connectivity",
                             labels={"educationLevel": "Education", "mean": "Avg Weighted Degree"},
                             color="mean", color_continuous_scale="Viridis")
        fig_edu_soc.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_edu_soc, use_container_width=True)

    st.markdown("""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #2E4057;">
    <strong>Evidence:</strong> Social connectivity varies by age — younger and middle-aged residents tend to
    have higher social activity. Education level shows a weak positive correlation with social connectivity.
    This suggests social engagement patterns are influenced by demographic factors.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Pattern 7: Key Influencers
    st.subheader("Pattern 7: Key Influencers — A Small Number of Bridge Individuals")

    betweenness = net_metrics["betweenness"]
    top_bridge = betweenness.nlargest(10, "betweenness_centrality")

    fig_bridge = px.bar(top_bridge.sort_values("betweenness_centrality"),
                        x="betweenness_centrality", y="participantId",
                        orientation="h",
                        title="Top 10 Bridge Individuals (Betweenness Centrality)",
                        labels={"betweenness_centrality": "Betweenness Centrality",
                                "participantId": "Participant ID"},
                        color="betweenness_centrality", color_continuous_scale="Reds",
                        text=top_bridge["betweenness_centrality"].round(6))
    fig_bridge.update_layout(height=400, yaxis=dict(type="category"))
    st.plotly_chart(fig_bridge, use_container_width=True)

    st.markdown("""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #E45756;">
    <strong>Evidence:</strong> A small number of individuals hold disproportionately high betweenness centrality —
    they act as bridges between different social circles. These "connectors" are critical for information
    flow and community cohesion. Targeting these individuals for community initiatives could be effective.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Pattern 8: Edge Weight Distribution
    st.subheader("Pattern 8: Interaction Frequency Heterogeneity")

    fig_ew = px.histogram(sn, x="weight", nbins=50,
                          title="Edge Weight Distribution (Interaction Frequency)",
                          color_discrete_sequence=[PALETTE["accent"]],
                          log_y=True)
    fig_ew.update_layout(height=400, xaxis_title="Edge Weight (interactions)", yaxis_title="Count (log scale)")
    st.plotly_chart(fig_ew, use_container_width=True)

    mean_w = sn["weight"].mean()
    median_w = sn["weight"].median()
    max_w = sn["weight"].max()
    st.markdown(f"""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #F58518;">
    <strong>Evidence:</strong> Edge weights span a wide range (mean={mean_w:.1f}, median={median_w:.0f}, max={max_w}).
    Most connections are weak (low interaction frequency), while a small number of relationships show
    very high interaction rates — consistent with Dunbar's number theory where strong ties are limited.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Pattern 9: Travel Purpose Patterns
    st.subheader("Pattern 9: Travel Purposes — Social/Recreation is Primary")

    col_l, col_r = st.columns(2)
    with col_l:
        fig_tp_bar = px.bar(tp, x="purpose", y="count",
                            title="Travel by Purpose",
                            labels={"purpose": "Purpose", "count": "Number of Trips"},
                            color="count", color_continuous_scale="Blues",
                            text=tp["count"])
        fig_tp_bar.update_layout(height=400, showlegend=False, xaxis_tickangle=-30)
        st.plotly_chart(fig_tp_bar, use_container_width=True)

    with col_r:
        fig_tp_cost = px.bar(tp, x="purpose", y="total_spent",
                             title="Total Spending by Travel Purpose",
                             labels={"purpose": "Purpose", "total_spent": "Total Spent ($)"},
                             color="total_spent", color_continuous_scale="Reds",
                             text=tp["total_spent"].round(0))
        fig_tp_cost.update_layout(height=400, showlegend=False, xaxis_tickangle=-30)
        st.plotly_chart(fig_tp_cost, use_container_width=True)

    st.markdown("""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #54A24B;">
    <strong>Evidence:</strong> Social/recreational travel dominates in both frequency and spending, reinforcing
    the picture of an active social community. Commuting (work-related travel) is secondary,
    suggesting many residents may live close to their workplaces.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Pattern 10: Geographic Clustering
    st.subheader("Pattern 10: Geographic Distribution of Social Venues")

    if base_map:
        fig_map = go.Figure()
        fig_map.add_layout_image(
            dict(source=f"data:image/png;base64,{base_map}",
                 xref="x", yref="y", x=-5000, y=8000,
                 sizex=10000, sizey=10000, sizing="stretch", layer="below")
        )

        venue_colors = {"Pub": "#E45756", "Restaurant": "#54A24B", "School": "#4C78A8"}
        venue_symbols = {"Pub": "circle", "Restaurant": "triangle-up", "School": "diamond"}

        for vt, color in venue_colors.items():
            if vt == "Pub" and "pubs" in data:
                df_v = data["pubs"]
                fig_map.add_trace(go.Scatter(
                    x=df_v["x"], y=df_v["y"], mode="markers",
                    name=vt, marker=dict(color=color, size=10, symbol="circle"),
                    text="Pub " + df_v["pubId"].astype(str), hoverinfo="text"
                ))
            elif vt == "Restaurant" and "restaurants" in data:
                df_v = data["restaurants"]
                fig_map.add_trace(go.Scatter(
                    x=df_v["x"], y=df_v["y"], mode="markers",
                    name=vt, marker=dict(color=color, size=10, symbol="triangle-up"),
                    text="Rest " + df_v["restaurantId"].astype(str), hoverinfo="text"
                ))
            elif vt == "School" and "schools" in data:
                df_v = data["schools"]
                fig_map.add_trace(go.Scatter(
                    x=df_v["x"], y=df_v["y"], mode="markers",
                    name=vt, marker=dict(color=color, size=12, symbol="diamond"),
                    text="School " + df_v["schoolId"].astype(str), hoverinfo="text"
                ))

        fig_map.update_layout(
            xaxis=dict(range=[-5000, 5000], showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(range=[0, 8000], showgrid=False, zeroline=False, showticklabels=False),
            height=550, margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            title="Venue Geographic Distribution"
        )
        st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #4C78A8;">
    <strong>Evidence:</strong> Venues cluster around specific geographic zones. Pubs and restaurants show
    spatial co-location patterns — suggesting commercial/social districts. Schools are fewer and more
    dispersed, serving larger catchment areas.
    </div>
    """, unsafe_allow_html=True)

    # Q2 Summary
    st.markdown("---")
    st.subheader("Q2 Summary: 10 Social Patterns Identified")
    st.markdown("""
    1. **Heavy-tailed degree distribution** — power-law characteristic of real social networks
    2. **Strong community structure** — high modularity, distinct social clusters
    3. **High local clustering** — tight-knit friend groups, "friends-of-friends" pattern
    4. **Venue type preference** — eating/drinking venues dominate social activity
    5. **Diurnal activity rhythm** — peak social activity in afternoon/evening hours
    6. **Demographic influence** — age and education correlate with social connectivity
    7. **Key bridge individuals** — a few people connect disparate communities
    8. **Interaction heterogeneity** — most ties are weak, few are very strong (Dunbar pattern)
    9. **Social/recreational travel dominance** — primary motivation for mobility
    10. **Geographic venue clustering** — social venues concentrate in specific districts
    """)


# ============================================================
# Q3: Business & Economy
# ============================================================
elif page.startswith("🏭"):
    st.title("Q3: Business & Economy")
    st.markdown("*Identify the predominant business base of the town. Describe patterns you identify.*")

    # --- Economic overview metrics ---
    total_wage = fin[fin["category"] == "Wage"]["total_amount"].sum()
    total_shelter = abs(fin[fin["category"] == "Shelter"]["total_amount"].sum())
    total_food = abs(fin[fin["category"] == "Food"]["total_amount"].sum())
    total_recreation = abs(fin[fin["category"] == "Recreation"]["total_amount"].sum())
    total_edu = abs(fin[fin["category"] == "Education"]["total_amount"].sum())
    total_spending = abs(fin[fin["category"] != "Wage"]["total_amount"].sum())
    total_jobs = js["employee_count"].sum()
    jobs_per_resident = total_jobs / len(ps)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Annual Wages", f"${total_wage:,.0f}")
    with col2:
        st.metric("Total Employers", f"{len(js):,}", help="Avg 5.2 employees each")
    with col3:
        st.metric("Total Jobs", f"{total_jobs:,}", help=f"{jobs_per_resident:.1f} jobs per resident")
    with col4:
        st.metric("Net Cash Flow", f"${total_wage - total_spending:,.0f}",
                  delta=f"{(total_wage - total_spending)/total_wage*100:.0f}% of wages")

    st.markdown("---")

    # Finding 1: Small Business Economy
    st.subheader("Finding 1: A Small Business Economy — No Large Employers")

    # Employer size distribution
    emp_size_dist = js["employee_count"].value_counts().sort_index()
    fig_emp_dist = px.bar(x=emp_size_dist.index.astype(str), y=emp_size_dist.values,
                          title=f"Employer Size Distribution ({len(js)} employers, avg {js['employee_count'].mean():.1f} employees)",
                          labels={"x": "Number of Employees", "y": "Number of Employers"},
                          color=emp_size_dist.values, color_continuous_scale="Blues",
                          text=emp_size_dist.values)
    fig_emp_dist.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_emp_dist, use_container_width=True)

    min_e = int(js["employee_count"].min())
    max_e = int(js["employee_count"].max())
    st.markdown(f"""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #4C78A8;">
    <strong>Key Finding — Predominant Business Base: Small-scale service businesses.</strong><br>
    All {len(js)} employers have between {min_e} and {max_e} employees (mean {js['employee_count'].mean():.1f},
    median {js['employee_count'].median():.0f}). There are <strong>no large corporations or factories</strong> —
    this is an economy of small shops, local services, and micro-enterprises.
    Total jobs: {total_jobs:,} for {len(ps):,} residents ({jobs_per_resident:.1f} jobs/resident),
    suggesting some residents hold multiple positions.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Finding 2: Financial Flow
    st.subheader("Finding 2: Financial Structure — Wage Income, Shelter & Recreation Spending")

    col_l, col_r = st.columns(2)
    with col_l:
        fin_sorted = fin.copy()
        fin_sorted = fin_sorted.sort_values("total_amount", ascending=True)
        fig_fin = px.bar(fin_sorted, y="category", x="total_amount",
                         title="Net Financial Flow by Category",
                         color="total_amount",
                         color_continuous_scale="RdBu",
                         orientation="h",
                         text=fin_sorted["total_amount"].apply(lambda x: f"${x:,.0f}"))
        fig_fin.add_vline(x=0, line_color="black")
        fig_fin.update_layout(height=420)
        st.plotly_chart(fig_fin, use_container_width=True)

    with col_r:
        # Expense breakdown (excl wage)
        expenses = fin[fin["total_amount"] < 0].copy()
        expenses["abs_amount"] = expenses["total_amount"].abs()
        fig_exp = px.pie(values=expenses["abs_amount"], names=expenses["category"],
                         title="Expense Breakdown by Category",
                         color_discrete_sequence=px.colors.qualitative.Set2)
        fig_exp.update_layout(height=420)
        st.plotly_chart(fig_exp, use_container_width=True)

    shelter_pct = total_shelter / total_spending * 100
    rec_pct = total_recreation / total_spending * 100
    food_pct = total_food / total_spending * 100
    st.markdown(f"""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #F58518;">
    <strong>Analysis:</strong> Wages (${total_wage:,.0f}) are the sole income source. Top 3 expenses:
    <strong>Shelter</strong> ${total_shelter:,.0f} ({shelter_pct:.0f}% of spending),
    <strong>Recreation</strong> ${total_recreation:,.0f} ({rec_pct:.0f}%),
    <strong>Food</strong> ${total_food:,.0f} ({food_pct:.0f}%).
    Recreation spending nearly equals food — suggesting an active social/leisure culture.
    Education is comparatively small at ${total_edu:,.0f} ({total_edu/total_spending*100:.1f}%).
    Net surplus of ${total_wage - total_spending:,.0f} ({(total_wage - total_spending)/total_wage*100:.0f}% of wages)
    indicates either high savings rate or incomplete expense tracking in the dataset.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Finding 3: Wage Analysis
    st.subheader("Finding 3: Wage Distribution — Moderate Range, Near-Normal")

    col_l, col_r = st.columns(2)
    with col_l:
        fig_wd = px.histogram(js, x="avg_hourly_rate", nbins=35,
                              title="Average Hourly Rate Distribution",
                              labels={"avg_hourly_rate": "Hourly Rate ($)"},
                              color_discrete_sequence=[PALETTE["green"]])
        fig_wd.add_vline(x=js["avg_hourly_rate"].mean(), line_dash="dash",
                         line_color=PALETTE["red"],
                         annotation_text=f"Mean: ${js['avg_hourly_rate'].mean():.2f}")
        fig_wd.add_vline(x=js["avg_hourly_rate"].median(), line_dash="dot",
                         line_color=PALETTE["accent"],
                         annotation_text=f"Median: ${js['avg_hourly_rate'].median():.2f}")
        fig_wd.update_layout(height=400)
        st.plotly_chart(fig_wd, use_container_width=True)

    with col_r:
        # Employer size vs wage - labeled
        js_plot = js.copy()
        js_plot["size_label"] = js_plot["employee_count"].apply(
            lambda x: "2-3 emp" if x <= 3 else ("4-6 emp" if x <= 6 else "7-9 emp"))
        fig_box = px.box(js_plot, x="size_label", y="avg_hourly_rate",
                         title="Wage Distribution by Employer Size",
                         color="size_label",
                         labels={"size_label": "Employer Size", "avg_hourly_rate": "Hourly Rate ($)"},
                         points="outliers")
        fig_box.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)

    wage_range = js["avg_hourly_rate"].max() - js["avg_hourly_rate"].min()
    st.markdown(f"""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #54A24B;">
    <strong>Analysis:</strong> Wages range from ${js['avg_hourly_rate'].min():.2f} to ${js['avg_hourly_rate'].max():.2f}/hr
    (span: ${wage_range:.2f}), with mean ${js['avg_hourly_rate'].mean():.2f} and median ${js['avg_hourly_rate'].median():.2f}.
    The near-normal distribution means most jobs cluster around the mean — extreme low/high wages are rare.
    Employer size shows <strong>no significant correlation</strong> with wage level: some small employers pay
    premium wages while some of the largest (9 employees) pay below average. Compensation appears
    driven by job type rather than employer scale.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Finding 4: Building & Business Mix
    st.subheader("Finding 4: Building Mix — Balanced Residential-Commercial")

    col_l, col_r = st.columns(2)
    with col_l:
        bt_pct = bt.copy()
        bt_pct["pct"] = (bt_pct["count"] / bt_pct["count"].sum() * 100).round(1)
        fig_bt = px.pie(values=bt["count"], names=bt["buildingType"],
                        title=f"Building Types ({bt['count'].sum()} total)",
                        color_discrete_sequence=px.colors.qualitative.Set3)
        fig_bt.update_traces(textposition="inside", textinfo="percent+label")
        fig_bt.update_layout(height=400)
        st.plotly_chart(fig_bt, use_container_width=True)

    with col_r:
        # Commercial buildings vs employers
        bt_dict = dict(zip(bt["buildingType"], bt["count"]))
        commercial = bt_dict.get("Commercial", 0)
        residential = bt_dict.get("Residental", 0)
        schools = bt_dict.get("School", 0)

        comp_data = pd.DataFrame({
            "Metric": ["Residential\nBuildings", "Commercial\nBuildings", "Employers\n(in Commercial)", "Unoccupied\nCommercial"],
            "Count": [residential, commercial, len(js), max(0, commercial - len(js))]
        })
        fig_comp = px.bar(comp_data, x="Metric", y="Count",
                          title=f"Commercial Space Utilization ({commercial} buildings for {len(js)} employers)",
                          color="Count", color_continuous_scale="Viridis",
                          text="Count")
        fig_comp.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_comp, use_container_width=True)

    vacancy = max(0, commercial - len(js))
    st.markdown(f"""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #72B7B2;">
    <strong>Analysis:</strong> Building stock is evenly split: {residential} residential ({residential/bt['count'].sum()*100:.0f}%),
    {commercial} commercial ({commercial/bt['count'].sum()*100:.0f}%), {schools} schools.
    With {len(js)} employers and {commercial} commercial buildings, there are <strong>{vacancy} more commercial buildings
    than employers</strong> — suggesting some commercial spaces are either unoccupied, shared by multiple
    enterprises, or used for non-business purposes. The town has physical capacity for economic growth.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Finding 5: Spending by Transaction Pattern
    st.subheader("Finding 5: Spending Patterns — Food is High-Frequency, Shelter is High-Value")

    col_l, col_r = st.columns(2)
    with col_l:
        fin_plot = fin.copy()
        fig_txn = px.bar(fin_plot.sort_values("transaction_count"), y="category", x="transaction_count",
                         title="Transaction Count by Category",
                         orientation="h",
                         color="transaction_count", color_continuous_scale="Blues",
                         text=fin_plot["transaction_count"].apply(lambda x: f"{x:,}"))
        fig_txn.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_txn, use_container_width=True)

    with col_r:
        fig_avg = px.bar(fin_plot.sort_values("avg_amount".abs()), y="category", x=fin_plot["avg_amount"].abs(),
                         title="Average Transaction Amount by Category",
                         orientation="h",
                         color=fin_plot["avg_amount"].abs(), color_continuous_scale="Reds",
                         text=fin_plot["avg_amount"].apply(lambda x: f"${abs(x):,.0f}"))
        fig_avg.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_avg, use_container_width=True)

    food_avg = abs(fin[fin["category"] == "Food"]["avg_amount"].iloc[0])
    shelter_avg = abs(fin[fin["category"] == "Shelter"]["avg_amount"].iloc[0])
    st.markdown(f"""
    <div style="background:#f0f4f8; padding:12px 16px; border-radius:8px; border-left:4px solid #B279A2;">
    <strong>Analysis:</strong> Food transactions are high-volume, low-value (~${food_avg:.0f}/txn) — daily purchases.
    Shelter payments are low-volume, high-value (~${shelter_avg:.0f}/txn) — monthly rent/mortgage.
    This bifurcation is characteristic of a normal consumer economy. The high food transaction count
    ({fin[fin['category']=='Food']['transaction_count'].iloc[0]:,}) relative to other categories suggests
    residents eat out or buy food frequently rather than in bulk.
    </div>
    """, unsafe_allow_html=True)

    # Q3 Summary
    st.markdown("---")
    st.subheader("Q3 Summary: The Predominant Business Base")
    st.markdown(f"""
    **EngageTown's economy is a small-business service economy** — not dominated by any single industry
    or large employer, but by {len(js)} micro-enterprises each employing {js['employee_count'].min():.0f}–{js['employee_count'].max():.0f} people.

    **Key characteristics:**
    - **Small-business dominance:** All {len(js)} employers are micro-enterprises (max {max_e} employees).
      No factories, no corporate headquarters — this is a town of local shops, services, and small offices.
    - **Building stock:** {residential} residential + {commercial} commercial + {schools} school buildings.
      Nearly balanced mix, with {vacancy} more commercial spaces than registered employers.
    - **Wage structure:** ${js['avg_hourly_rate'].min():.2f}–${js['avg_hourly_rate'].max():.2f}/hr (mean ${js['avg_hourly_rate'].mean():.2f}).
      Compensation is not driven by employer size — small firms can be high-paying.
    - **Spending:** Shelter (${total_shelter:,.0f}) > Recreation (${total_recreation:,.0f}) > Food (${total_food:,.0f}).
      High recreation spend relative to food signals an active leisure culture.
    - **Economic capacity:** {vacancy} surplus commercial buildings + ${total_wage - total_spending:,.0f} net cash surplus
      suggest room for economic expansion.

    **Bottom line:** EngageTown is a <strong>balanced, small-scale service economy</strong> — best described
    as a community of small businesses serving local residents, with no dominant industrial sector.
    """)


# ============================================================
# Q4: Town Summary
# ============================================================
elif page.startswith("📋"):
    st.title("Q4: Town Summary")
    st.markdown("*A one-page summary of key information for EngageTown residents.*")

    # ---- Hero Banner ----
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; padding:20px; background:linear-gradient(135deg, #2E4057 0%, #4C78A8 100%);
    border-radius:12px; color:white; margin-bottom:20px;">
        <h1 style="color:white; margin:0; font-size:2.5em;">🏙️ Welcome to EngageTown</h1>
        <p style="font-size:1.2em; opacity:0.9; margin-top:8px;">Your Community at a Glance</p>
    </div>
    """, unsafe_allow_html=True)

    # ---- Key Metrics Row ----
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Population", f"{len(ps):,}", help="Total residents (volunteers)")
    with col2:
        st.metric("📊 Avg Age", f"{ps['age'].mean():.0f} years", help="Average resident age")
    with col3:
        st.metric("🏢 Employers", f"{len(js):,}", help="Total employers in town")
    with col4:
        st.metric("📍 Venues", f"{len(vc):,}", help="Total social venues")

    st.markdown("---")

    # ---- Three-Column Layout ----
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 👥 Who We Are")
        st.markdown(f"""
        - **Population:** {len(ps):,} residents
        - **Age range:** {ps['age'].min():.0f}–{ps['age'].max():.0f} (avg {ps['age'].mean():.1f})
        - **Households:** avg {ps['householdSize'].mean():.1f} persons
        - **Families with kids:** {ps['haveKids'].eq(True).mean()*100:.0f}%
        - **Education:** Mostly High School through Bachelors
        - **Interest groups:** {ps['interestGroup'].nunique()} (evenly distributed A–J)
        """)

        # Mini age pyramid
        age_bins = [0, 18, 30, 45, 60, 100]
        age_labels = ["0-17", "18-29", "30-44", "45-59", "60+"]
        ps_m = ps.copy()
        ps_m["age_group"] = pd.cut(ps_m["age"], bins=age_bins, labels=age_labels)
        age_summary = ps_m["age_group"].value_counts().sort_index()
        fig_mini_age = px.bar(x=age_summary.index, y=age_summary.values,
                              color_discrete_sequence=[PALETTE["secondary"]],
                              labels={"x": "", "y": ""})
        fig_mini_age.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
        st.plotly_chart(fig_mini_age, use_container_width=True)

    with col2:
        st.markdown("### 🤝 How We Live")
        total_checkins = vc["checkins"].sum()
        social_checkins = vc[vc["venueType"].isin(["Restaurant", "Pub"])]["checkins"].sum()
        social_pct = social_checkins / total_checkins * 100

        st.markdown(f"""
        - **Total check-ins:** {total_checkins:,}
        - **Social venues (Restaurant+Pub):** {social_checkins:,} ({social_pct:.0f}% of all)
        - **Network:** {net_metrics['num_edges']:,} relationships, {net_metrics.get('num_communities', 'N/A')} communities
        - **Modularity:** {net_metrics.get('modularity', 0):.4f} (strong community structure)
        - **Avg clustering:** {net_metrics['avg_clustering']:.4f} (tight-knit friend groups)
        - **Venues:** {len(data.get('pubs', []))} Pubs | {len(data.get('restaurants', []))} Restaurants | {len(data.get('schools', []))} Schools
        """)

        # Mini venue type chart
        vt_mini = vc.groupby("venueType")["checkins"].sum().sort_values(ascending=True)
        fig_mini_vt = px.bar(x=vt_mini.values, y=vt_mini.index,
                             color_discrete_sequence=[PALETTE["green"]],
                             labels={"x": "", "y": ""}, orientation="h")
        fig_mini_vt.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
        st.plotly_chart(fig_mini_vt, use_container_width=True)

    with col3:
        st.markdown("### 💰 Our Economy")
        total_wages = fin[fin["category"] == "Wage"]["total_amount"].sum()
        avg_wage = js["avg_hourly_rate"].mean()
        total_jobs_q4 = js["employee_count"].sum()

        st.markdown(f"""
        - **Annual wages:** ${total_wages:,.0f}
        - **Avg hourly rate:** ${avg_wage:.2f} (${js['avg_hourly_rate'].min():.2f}–${js['avg_hourly_rate'].max():.2f})
        - **Total jobs:** {total_jobs_q4:,} across {len(js)} small employers
        - **Top expense:** Shelter (${abs(fin[fin['category']=='Shelter']['total_amount'].iloc[0]):,.0f})
        - **Building stock:** {bt['count'].sum():,} buildings ({dict(zip(bt['buildingType'], bt['count']))})
        """)

        # Mini financial pie
        fin_pie = fin[fin["category"] != "Wage"].copy()
        fig_mini_fin = px.pie(values=fin_pie["total_amount"].abs(),
                              names=fin_pie["category"],
                              color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_mini_fin.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0), showlegend=True,
                                   legend=dict(font=dict(size=8)))
        st.plotly_chart(fig_mini_fin, use_container_width=True)

    st.markdown("---")

    # ---- Map ----
    st.markdown("### 🗺️ Our Town Map")
    st.caption("Key venues and community landmarks")

    if base_map:
        fig_map = go.Figure()
        fig_map.add_layout_image(
            dict(source=f"data:image/png;base64,{base_map}",
                 xref="x", yref="y", x=-5000, y=8000,
                 sizex=10000, sizey=10000, sizing="stretch", layer="below")
        )

        if "pubs" in data:
            pubs_df = data["pubs"]
            fig_map.add_trace(go.Scatter(
                x=pubs_df["x"], y=pubs_df["y"], mode="markers",
                name="Pubs", marker=dict(color="#E45756", size=10, symbol="circle"),
                text="Pub " + pubs_df["pubId"].astype(str), hoverinfo="text"
            ))

        if "restaurants" in data:
            rest_df = data["restaurants"]
            fig_map.add_trace(go.Scatter(
                x=rest_df["x"], y=rest_df["y"], mode="markers",
                name="Restaurants", marker=dict(color="#54A24B", size=10, symbol="triangle-up"),
                text="Restaurant " + rest_df["restaurantId"].astype(str), hoverinfo="text"
            ))

        if "schools" in data:
            sch_df = data["schools"]
            fig_map.add_trace(go.Scatter(
                x=sch_df["x"], y=sch_df["y"], mode="markers",
                name="Schools", marker=dict(color="#4C78A8", size=14, symbol="diamond"),
                text="School " + sch_df["schoolId"].astype(str), hoverinfo="text"
            ))

        fig_map.update_layout(
            xaxis=dict(range=[-5000, 5000], showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(range=[0, 8000], showgrid=False, zeroline=False, showticklabels=False),
            height=500, margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            title="EngageTown Venue Map"
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Map not available (BaseMap.png missing)")

    st.markdown("---")

    # ---- Bottom summary ----
    max_emp = int(js["employee_count"].max())
    bt_dict = dict(zip(bt["buildingType"], bt["count"]))
    st.markdown(f"""
    <div style="background:#f0f4f8; padding:16px 20px; border-radius:12px; text-align:center;">
    <strong>EngageTown at a Glance:</strong>
    {len(ps):,} residents | {ps["age"].mean():.0f} avg age | {ps["householdSize"].mean():.1f} avg household |
    {net_metrics["num_edges"]:,} social connections | ${total_wages:,.0f} annual wages |
    {len(js)} micro-employers (max {max_emp} employees) | {bt_dict}
    </div>
    """, unsafe_allow_html=True)
# ============================================================
# Footer
# ============================================================
st.markdown("---")
st.caption("VAST Challenge 2022 MC1 | Visual Analytics Report | Python · Streamlit · Plotly · NetworkX")
