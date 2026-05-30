"""
VAST Challenge 2022 MC1 - Interactive Dashboard
Streamlit app for visualizing EngageTown data
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# networkx only needed if doing graph analysis
from pathlib import Path
import base64
from io import BytesIO

st.set_page_config(
    page_title="EngageTown Dashboard | VAST 2022 MC1",
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
    """Load all processed data files."""
    data = {}
    for f in PROCESSED.glob("*.parquet"):
        key = f.stem
        data[key] = pd.read_parquet(f)
    return data

@st.cache_data
def load_base_map():
    """Load base map as base64."""
    map_path = BASE / "BaseMap.png"
    if map_path.exists():
        with open(map_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# ============================================================
# Sidebar
# ============================================================
st.sidebar.title("🏙️ EngageTown Dashboard")
st.sidebar.markdown("VAST Challenge 2022 — Mini-Challenge 1")
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

# ============================================================
# Load data
# ============================================================
try:
    data = load_data()
    base_map = load_base_map()
    data_loaded = True
except Exception as e:
    st.error(f"Data not yet processed. Run data_processor.py first.\n\nError: {e}")
    st.info("Run: `python3 data_processor.py`")
    data_loaded = False

if not data_loaded:
    st.stop()

# ============================================================
# Q1: Demographics
# ============================================================
if page.startswith("📊"):
    st.title("Q1: Town Demographics")
    st.markdown("Characterizing the population of EngageTown based on volunteer data.")

    ps = data["participant_summary"]

    # Row 1: Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Population (Volunteers)", f"{len(ps):,}")
    with col2:
        st.metric("Average Age", f"{ps['age'].mean():.1f}")
    with col3:
        st.metric("Avg Household Size", f"{ps['householdSize'].mean():.1f}")
    with col4:
        kids_pct = ps['haveKids'].eq(True).mean() * 100
        st.metric("Have Kids", f"{kids_pct:.1f}%")
    with col5:
        st.metric("Avg Joviality", f"{ps['joviality'].mean():.3f}")

    st.markdown("---")

    # Row 2: Age & Education distributions
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Age Distribution")
        fig_age = px.histogram(ps, x="age", nbins=30, color_discrete_sequence=["#4C78A8"],
                               title="Population Age Distribution")
        fig_age.update_layout(bargap=0.1, height=400)
        st.plotly_chart(fig_age, use_container_width=True)

    with col_right:
        st.subheader("Education Level")
        edu_counts = ps["educationLevel"].value_counts()
        fig_edu = px.pie(values=edu_counts.values, names=edu_counts.index,
                         title="Education Distribution",
                         color_discrete_sequence=px.colors.qualitative.Set2)
        fig_edu.update_layout(height=400)
        st.plotly_chart(fig_edu, use_container_width=True)

    # Row 3: Household & Interest
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Household Size Distribution")
        hh_counts = ps["householdSize"].value_counts().sort_index()
        fig_hh = px.bar(x=hh_counts.index, y=hh_counts.values,
                        labels={"x": "Household Size", "y": "Count"},
                        title="Household Size Distribution",
                        color_discrete_sequence=["#54A24B"])
        fig_hh.update_layout(height=400)
        st.plotly_chart(fig_hh, use_container_width=True)

    with col_right:
        st.subheader("Interest Groups")
        interest_counts = ps["interestGroup"].value_counts().sort_index()
        fig_int = px.bar(x=interest_counts.index, y=interest_counts.values,
                         labels={"x": "Interest Group", "y": "Count"},
                         title="Interest Group Distribution",
                         color_discrete_sequence=["#E45756"])
        fig_int.update_layout(height=400)
        st.plotly_chart(fig_int, use_container_width=True)

    # Row 4: Financial status & balance
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Average Balance Distribution")
        if "avg_balance" in ps.columns:
            fig_bal = px.histogram(ps, x="avg_balance", nbins=50,
                                   title="Average Available Balance",
                                   color_discrete_sequence=["#F58518"])
            fig_bal.update_layout(height=400)
            st.plotly_chart(fig_bal, use_container_width=True)

    with col_right:
        st.subheader("Social Connectivity (Degree)")
        if "social_degree" in ps.columns:
            fig_deg = px.histogram(ps[ps["social_degree"] > 0], x="social_degree", nbins=40,
                                   title="Social Network Degree Distribution",
                                   color_discrete_sequence=["#72B7B2"])
            fig_deg.update_layout(height=400)
            st.plotly_chart(fig_deg, use_container_width=True)

# ============================================================
# Q2: Social Activities
# ============================================================
elif page.startswith("🤝"):
    st.title("Q2: Social Activities & Networks")
    st.markdown("Analyzing social patterns, popular venues, and community interactions.")

    # Row 1: Venue checkins
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Top Venues by Check-ins")
        vc = data["venue_checkins"]
        top_venues = vc.nlargest(15, "checkins")
        fig_vc = px.bar(top_venues, x="venueId", y="checkins", color="venueType",
                        title="Top 15 Most Visited Venues",
                        color_discrete_sequence=px.colors.qualitative.Plotly)
        fig_vc.update_layout(height=450)
        st.plotly_chart(fig_vc, use_container_width=True)

    with col_right:
        st.subheader("Check-ins by Venue Type")
        venue_type_counts = vc.groupby("venueType")["checkins"].sum().sort_values(ascending=False)
        fig_vt = px.pie(values=venue_type_counts.values, names=venue_type_counts.index,
                        title="Total Check-ins by Venue Type",
                        color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_vt.update_layout(height=450)
        st.plotly_chart(fig_vt, use_container_width=True)

    # Row 2: Social Network
    st.markdown("---")
    st.subheader("Social Network Analysis")

    sn = data["social_network"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Edges", f"{len(sn):,}")
    with col2:
        st.metric("Avg Edge Weight", f"{sn['weight'].mean():.1f}")
    with col3:
        st.metric("Max Edge Weight", f"{sn['weight'].max()}")

    # Network degree distribution
    col_left, col_right = st.columns(2)

    with col_left:
        # Degree distribution
        ps = data["participant_summary"]
        if "social_degree" in ps.columns:
            fig_deg = px.histogram(ps[ps["social_degree"] > 0], x="social_degree", nbins=50,
                                   title="Social Degree Distribution (log scale)",
                                   color_discrete_sequence=["#72B7B2"],
                                   log_y=True)
            fig_deg.update_layout(height=400)
            st.plotly_chart(fig_deg, use_container_width=True)

    with col_right:
        # Edge weight distribution
        fig_ew = px.histogram(sn, x="weight", nbins=50,
                              title="Edge Weight Distribution (interaction frequency)",
                              color_discrete_sequence=["#B279A2"],
                              log_y=True)
        fig_ew.update_layout(height=400)
        st.plotly_chart(fig_ew, use_container_width=True)

    # Row 3: Travel purposes
    st.markdown("---")
    st.subheader("Travel Patterns")

    col_left, col_right = st.columns(2)

    with col_left:
        tp = data["travel_purpose_summary"]
        fig_tp = px.bar(tp, x="purpose", y="count",
                        title="Travel by Purpose",
                        color_discrete_sequence=["#FF9DA6"])
        fig_tp.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_tp, use_container_width=True)

    with col_right:
        if "total_spent" in tp.columns:
            fig_ts = px.bar(tp, x="purpose", y="total_spent",
                            title="Total Spending by Travel Purpose",
                            color_discrete_sequence=["#54A24B"])
            fig_ts.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_ts, use_container_width=True)

# ============================================================
# Q3: Business & Economy
# ============================================================
elif page.startswith("🏭"):
    st.title("Q3: Business & Economy")
    st.markdown("Identifying the predominant business base and economic patterns.")

    # Row 1: Financial overview
    fin = data["financial_summary"]

    col1, col2, col3 = st.columns(3)
    with col1:
        total_wage = fin[fin["category"] == "Wage"]["total_amount"].sum()
        st.metric("Total Wages", f"${total_wage:,.0f}")
    with col2:
        total_shelter = abs(fin[fin["category"] == "Shelter"]["total_amount"].sum())
        st.metric("Total Shelter Spending", f"${total_shelter:,.0f}")
    with col3:
        total_edu = abs(fin[fin["category"] == "Education"]["total_amount"].sum())
        st.metric("Total Education Spending", f"${total_edu:,.0f}")

    st.markdown("---")

    # Financial categories
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Financial Categories Overview")
        fin_sorted = fin.sort_values("total_amount", ascending=True)
        fin_sorted["abs_amount"] = fin_sorted["total_amount"].abs()
        fig_fin = px.bar(fin_sorted, y="category", x="total_amount",
                         title="Total Amount by Category",
                         color="total_amount",
                         color_continuous_scale="RdBu",
                         orientation="h")
        fig_fin.update_layout(height=500)
        st.plotly_chart(fig_fin, use_container_width=True)

    with col_right:
        st.subheader("Transaction Count by Category")
        fig_tc = px.bar(fin.sort_values("transaction_count", ascending=True),
                        y="category", x="transaction_count",
                        title="Number of Transactions by Category",
                        color_discrete_sequence=["#4C78A8"],
                        orientation="h")
        fig_tc.update_layout(height=500)
        st.plotly_chart(fig_tc, use_container_width=True)

    # Row 2: Employer analysis
    st.markdown("---")
    st.subheader("Employer Analysis")

    js = data["job_summary"]

    col_left, col_right = st.columns(2)

    with col_left:
        top_emps = js.nlargest(15, "employee_count")
        fig_emp = px.bar(top_emps, x="employerId", y="employee_count",
                         title="Top 15 Employers by Employee Count",
                         color_discrete_sequence=["#F58518"])
        fig_emp.update_layout(height=400)
        st.plotly_chart(fig_emp, use_container_width=True)

    with col_right:
        fig_wage = px.scatter(js, x="employee_count", y="avg_hourly_rate",
                              title="Employer Size vs Average Wage",
                              labels={"employee_count": "Employee Count",
                                      "avg_hourly_rate": "Avg Hourly Rate ($)"},
                              color_discrete_sequence=["#72B7B2"],
                              opacity=0.6)
        fig_wage.update_layout(height=400)
        st.plotly_chart(fig_wage, use_container_width=True)

    # Row 3: Building types
    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        bt = data["building_types"]
        fig_bt = px.pie(values=bt["count"], names=bt["buildingType"],
                        title="Building Types Distribution",
                        color_discrete_sequence=px.colors.qualitative.Set3)
        fig_bt.update_layout(height=400)
        st.plotly_chart(fig_bt, use_container_width=True)

    with col_right:
        st.subheader("Wage Distribution by Job")
        fig_wd = px.histogram(js, x="avg_hourly_rate", nbins=40,
                              title="Average Hourly Rate Distribution",
                              color_discrete_sequence=["#E45756"])
        fig_wd.update_layout(height=400)
        st.plotly_chart(fig_wd, use_container_width=True)

# ============================================================
# Q4: Town Summary
# ============================================================
elif page.startswith("📋"):
    st.title("Q4: Town Summary")
    st.markdown("A one-page summary of key information for EngageTown residents.")

    ps = data["participant_summary"]
    fin = data["financial_summary"]
    vc = data["venue_checkins"]
    js = data["job_summary"]
    tp = data["travel_purpose_summary"]
    bt = data["building_types"]

    # Hero section
    st.markdown("---")
    st.header("🏙️ Welcome to EngageTown!")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Population", f"{len(ps):,}")
    with col2:
        st.metric("Avg Age", f"{ps['age'].mean():.0f}")
    with col3:
        st.metric("Employers", f"{len(js):,}")
    with col4:
        st.metric("Venues", f"{len(vc):,}")

    st.markdown("---")

    # Key insights
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📊 Who We Are")

        # Demographics summary
        edu_top = ps["educationLevel"].mode().iloc[0] if len(ps["educationLevel"].mode()) > 0 else "N/A"
        avg_hh = ps["householdSize"].mean()
        kids_pct = ps["haveKids"].eq(True).mean() * 100

        st.markdown(f"""
        - **Population:** {len(ps):,} residents
        - **Average Age:** {ps['age'].mean():.1f} years (range: {ps['age'].min():.0f}–{ps['age'].max():.0f})
        - **Most Common Education:** {edu_top}
        - **Average Household Size:** {avg_hh:.1f} persons
        - **Families with Children:** {kids_pct:.1f}%
        - **Interest Groups:** {', '.join(sorted(ps['interestGroup'].unique()))} ({len(ps['interestGroup'].unique())} groups)
        """)

        st.subheader("🏭 Our Economy")
        total_wages = fin[fin["category"] == "Wage"]["total_amount"].sum()
        num_jobs = len(js)
        avg_wage = js["avg_hourly_rate"].mean()

        st.markdown(f"""
        - **Total Annual Wages:** ${total_wages:,.0f}
        - **Number of Jobs:** {num_jobs:,}
        - **Average Hourly Rate:** ${avg_wage:.2f}
        - **Building Types:** {', '.join(f'{b} ({c})' for b, c in zip(bt['buildingType'], bt['count']))}
        """)

    with col_right:
        st.subheader("🤝 Our Social Life")
        top_venue_type = vc.groupby("venueType")["checkins"].sum().idxmax()
        total_checkins = vc["checkins"].sum()
        total_pubs = len(data.get("pubs", pd.DataFrame()))
        total_restaurants = len(data.get("restaurants", pd.DataFrame()))
        total_schools = len(data.get("schools", pd.DataFrame()))

        st.markdown(f"""
        - **Total Check-ins:** {total_checkins:,}
        - **Most Popular Venue Type:** {top_venue_type}
        - **Pubs:** {total_pubs}
        - **Restaurants:** {total_restaurants}
        - **Schools:** {total_schools}
        """)

        st.subheader("🚶 How We Travel")
        top_purpose = tp.iloc[0]["purpose"] if len(tp) > 0 else "N/A"
        total_trips = tp["count"].sum()

        st.markdown(f"""
        - **Total Trips Recorded:** {total_trips:,}
        - **Most Common Travel Purpose:** {top_purpose}
        - **Travel Purposes:** {len(tp)} types
        """)

        st.subheader("💰 Spending Patterns")
        fin_no_wage = fin[fin["category"] != "Wage"]
        top_spend = fin_no_wage.iloc[fin_no_wage["total_amount"].abs().argmax()]

        st.markdown(f"""
        - **Largest Expense Category:** {top_spend['category']} (${abs(top_spend['total_amount']):,.0f})
        """)

    # Map visualization
    st.markdown("---")
    st.subheader("🗺️ Town Map")

    if base_map:
        # Create map with venue overlay
        fig_map = go.Figure()

        # Add base map as background
        fig_map.add_layout_image(
            dict(
                source=f"data:image/png;base64,{base_map}",
                xref="x", yref="y",
                x=-5000, y=8000,
                sizex=10000, sizey=10000,
                sizing="stretch",
                layer="below"
            )
        )

        # Add pubs
        if "pubs" in data:
            pubs_df = data["pubs"]
            fig_map.add_trace(go.Scatter(
                x=pubs_df["x"], y=pubs_df["y"],
                mode="markers", name="Pubs",
                marker=dict(color="#E45756", size=8, symbol="circle"),
                text="Pub " + pubs_df["pubId"].astype(str),
                hoverinfo="text"
            ))

        # Add restaurants
        if "restaurants" in data:
            rest_df = data["restaurants"]
            fig_map.add_trace(go.Scatter(
                x=rest_df["x"], y=rest_df["y"],
                mode="markers", name="Restaurants",
                marker=dict(color="#54A24B", size=8, symbol="triangle-up"),
                text="Restaurant " + rest_df["restaurantId"].astype(str),
                hoverinfo="text"
            ))

        # Add schools
        if "schools" in data:
            sch_df = data["schools"]
            fig_map.add_trace(go.Scatter(
                x=sch_df["x"], y=sch_df["y"],
                mode="markers", name="Schools",
                marker=dict(color="#4C78A8", size=10, symbol="diamond"),
                text="School " + sch_df["schoolId"].astype(str),
                hoverinfo="text"
            ))

        fig_map.update_layout(
            xaxis=dict(range=[-5000, 5000], showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(range=[0, 8000], showgrid=False, zeroline=False, showticklabels=False),
            height=600,
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            title="EngageTown Venue Map"
        )

        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("BaseMap.png not found. Map visualization unavailable.")

# ============================================================
# Footer
# ============================================================
st.markdown("---")
st.caption("VAST Challenge 2022 MC1 | Interactive Dashboard | Built with Streamlit & Plotly")
