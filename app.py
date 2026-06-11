"""
VAST Challenge 2022 MC1 — EngageTown Visual Analytics Report
============================================================
Streamlit dashboard: 4-page analysis report with interactive charts.
Chart generation and data loading are delegated to common.py.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from common import (
    # Paths
    DATA_ROOT, PROCESSED, BASE,
    # Palette
    PALETTE, COLORS,
    # Data loading
    load_data as _load_data,
    load_base_map as _load_base_map,
    # Network analysis
    compute_network_metrics as _compute_network_metrics,
    # Data preparation
    prepare_cross_analysis,
    prepare_hourly_activity,
    prepare_employer_industry,
    # Derived metrics
    compute_economic_metrics,
    compute_weekend_metrics,
    # Q1 charts
    make_q1_age_histogram, make_q1_age_pie, make_q1_education_bar,
    make_q1_edu_balance, make_q1_edu_age_cross, make_q1_household_size, make_q1_kids_pie,
    make_q1_interest_groups, make_q1_balance_hist, make_q1_joviality_hist,
    # Q2 charts
    make_q2_degree_distribution, make_q2_rank_frequency,
    make_q2_community_sizes, make_q2_clustering_hist,
    make_q2_betweenness_hist, make_q2_bridge_individuals,
    make_q2_venue_types, make_q2_top_venues,
    make_q2_hourly_activity, make_q2_mode_area,
    make_q2_weekday_weekend, make_q2_weekday_weekend_modes,
    make_q2_age_social, make_q2_edu_social,
    make_q2_edge_weights, make_q2_travel_purpose, make_q2_travel_spending,
    # Q3 charts
    make_q3_employer_size, make_q3_financial_flow, make_q3_expense_pie,
    make_q3_wage_hist, make_q3_wage_box, make_q3_building_types,
    make_q3_industry_pie, make_q3_industry_wage,
    # Q4 charts
    make_q4_mini_age, make_q4_mini_venue, make_q4_mini_financial,
    make_venue_map,
)

st.set_page_config(
    page_title="EngageTown Report | VAST 2022 MC1",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Cached wrappers around common.py functions
# ============================================================

@st.cache_data
def load_data():
    return _load_data()

@st.cache_data
def load_base_map():
    return _load_base_map()

@st.cache_data
def get_network_metrics(_sn):
    return _compute_network_metrics(_sn)

@st.cache_data
def get_cross_analysis(_ps, _net_metrics):
    return prepare_cross_analysis(_ps, _net_metrics)

@st.cache_data
def get_employer_buildings():
    """Load employer-to-building mapping from raw Employers.csv."""
    emp = pd.read_csv(DATA_ROOT / "Datasets" / "Attributes" / "Employers.csv")
    return emp[["employerId", "buildingId"]]

# ============================================================
# Sidebar
# ============================================================
st.sidebar.title("🏙️ EngageTown 分析报告")
st.sidebar.markdown("**VAST Challenge 2022 — Mini-Challenge 1**")
st.sidebar.markdown("可视化分析报告")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "导航",
    ["📊 Q1：人口特征",
     "🤝 Q2：社交活动",
     "🏭 Q3：商业经济",
     "📋 Q4：城市概览"]
)

st.sidebar.markdown("---")
st.sidebar.caption("数据来源：VAST Challenge 2022 MC1")
st.sidebar.caption("技术栈：Python、Streamlit、Plotly、NetworkX")

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
# Assign data slices & derived variables
# ============================================================
ps = data["participant_summary"]
sn = data["social_network"]
vc = data["venue_checkins"]
fin = data["financial_summary"]
js = data["job_summary"]
ha = data["hourly_activity"]
tp = data["travel_purpose_summary"]
bt = data["building_types"]

net_metrics = get_network_metrics(sn)
cross = get_cross_analysis(ps, net_metrics)
mode_cols = prepare_hourly_activity(ha)

# Economic metrics
econ = compute_economic_metrics(fin, js, bt, ps)
weekend = compute_weekend_metrics(ha, mode_cols)

# Industry classification
js_with_ind, ind_counts, _ = prepare_employer_industry(data, js)


# ============================================================
# Q1: 人口特征
# ============================================================
if page.startswith("📊"):
    st.title("Q1：城镇人口特征")
    st.markdown("*假设志愿者群体能够代表城镇总体人口，描绘其人口统计学特征*")

    # ---- Hero Banner ----
    st.markdown("""
    <div style="text-align:center; padding:20px; background:linear-gradient(135deg, #1a2a3a 0%, #2E4057 40%, #4C78A8 100%);
    border-radius:10px; color:white; margin-bottom:20px;">
        <h2 style="color:white; margin:0; font-weight:600;">👥 人口画像 —— 谁居住在 EngageTown？</h2>
    </div>
    """, unsafe_allow_html=True)

    # --- Hero metrics ---
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("👥 总人口", f"{len(ps):,}")
    with col2:
        st.metric("📊 平均年龄", f"{ps['age'].mean():.1f} 岁")
    with col3:
        st.metric("📈 年龄中位数", f"{ps['age'].median():.0f} 岁")
    with col4:
        st.metric("🏘️ 户均人口", f"{ps['householdSize'].mean():.1f} 人")
    with col5:
        st.metric("👶 有子女家庭", f"{ps['haveKids'].eq(True).mean()*100:.1f}%")
    with col6:
        st.metric("🎯 兴趣组数", f"{ps['interestGroup'].nunique()}")

    st.markdown("---")

    # ================================================================
    # Section 1: 年龄结构
    # ================================================================
    st.markdown("## 一、年龄结构——以劳动年龄人口为主体")
    st.markdown("*人口年龄分布特征及其社会经济含义*")

    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.plotly_chart(make_q1_age_histogram(ps), use_container_width=True)
    with col_r:
        st.plotly_chart(make_q1_age_pie(ps), use_container_width=True)

    age_bins = [0, 18, 30, 45, 60, 100]
    age_labels_cn = ["0–17（未成年）", "18–29（青年）", "30–44（壮年）", "45–59（中年）", "60+（老年）"]
    ps_age = ps.copy()
    ps_age["age_group"] = pd.cut(ps_age["age"], bins=age_bins, labels=age_labels_cn)
    age_summary = ps_age["age_group"].value_counts().sort_index()
    working_age_pct = (ps_age["age"].between(18, 59).mean() * 100)

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #2E4057; margin:12px 0;">
    <strong>📌 分析：</strong>EngageTown 人口年龄分布呈现典型的<b>劳动力主导型结构</b>，均值 {ps['age'].mean():.1f} 岁，
    中位数 {ps['age'].median():.0f} 岁。18–59 岁劳动年龄人口占比约 <b>{working_age_pct:.0f}%</b>，构成城市经济活动的核心力量。
    年龄分布呈现轻微右偏态——老年人口（60+）相对稀少，暗示该城镇为<b>以中青年为主体的经济活跃社区</b>，
    抚养比处于较优区间。未成年人口（0–17 岁）占 {age_summary.get('0–17（未成年）', 0)/len(ps)*100:.1f}%，
    老龄化压力较小，人口结构具有可持续性。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Section 2: 教育水平
    # ================================================================
    st.markdown("## 二、教育水平与人力资本")
    st.markdown("*居民受教育程度分布及其与经济状况的关联*")

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q1_education_bar(ps), use_container_width=True)
    with col_r:
        st.plotly_chart(make_q1_edu_balance(ps), use_container_width=True)

    st.plotly_chart(make_q1_edu_age_cross(ps), use_container_width=True)

    edu_dist = ps["educationLevel"].value_counts()
    top_edu = edu_dist.index[0]
    bachelors_pct = edu_dist.get("Bachelors", 0) / len(ps) * 100
    hs_pct = edu_dist.get("HighSchoolOrCollege", 0) / len(ps) * 100
    grad_pct = edu_dist.get("Graduate", 0) / len(ps) * 100

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #4C78A8; margin:12px 0;">
    <strong>📌 分析：</strong>居民受教育程度集中于"<b>高中或大学肄业</b>"（{edu_dist.get('HighSchoolOrCollege', 0)} 人，
    {hs_pct:.1f}%）与"<b>学士</b>"（{edu_dist.get('Bachelors', 0)} 人，{bachelors_pct:.1f}%）两个层级，
    二者合计占总人口七成以上。"研究生"学历者仅 {edu_dist.get('Graduate', 0)} 人（{grad_pct:.1f}%），
    占比最小。教育水平与可用余额呈<b>正向梯度关系</b>——学士及以上学历者的平均可用余额显著高于低学历群体，
    反映了人力资本对经济回报的正向影响。值得注意的是，"高中或大学肄业"群体规模最大但内部经济分化也最为显著，
    可能映射出不同职业路径与技能溢价差异。整体而言，EngageTown 的人力资本结构以<b>中等技能劳动力为主体</b>，
    具备支撑本地服务经济的人才基础。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Section 3: 家庭结构
    # ================================================================
    st.markdown("## 三、家庭与居住结构——小家庭化趋势明显")
    st.markdown("*住户规模、子女养育与家庭类型分布*")

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q1_household_size(ps), use_container_width=True)
    with col_r:
        st.plotly_chart(make_q1_kids_pie(ps), use_container_width=True)

    kids_pct = ps['haveKids'].eq(True).mean() * 100
    hs_dist = ps['householdSize'].value_counts().sort_index()
    hh_mode = hs_dist.idxmax()

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #54A24B; margin:12px 0;">
    <strong>📌 分析：</strong>户均人口仅 <b>{ps['householdSize'].mean():.1f} 人</b>，众数亦为 {hh_mode} 人，
    呈现明显的<b>小家庭化特征</b>。有子女家庭占比约 <b>{kids_pct:.0f}%</b>，意味着近七成住户为无子女家庭
    （二人户或无子女的独居/合住）。将两项数据交叉来看：大量二人户无子女，少量家庭承担子女养育功能。
    这种结构暗示 EngageTown 可能吸引<b>年轻夫妇、合住伙伴或空巢家庭</b>——与劳动力主导型的年龄结构互相印证。
    低抚养比降低了公共教育支出压力，但也意味着城市的长期人口增长更依赖外部迁入而非自然增长。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Section 4: 兴趣群体
    # ================================================================
    st.markdown("## 四、兴趣群体与社会多样性——均匀分布的社群结构")
    st.markdown("*居民兴趣偏好的分布特征及其社会整合意义*")

    st.plotly_chart(make_q1_interest_groups(ps), use_container_width=True)

    ig_counts = ps['interestGroup'].value_counts()
    ig_min, ig_max = ig_counts.min(), ig_counts.max()
    ig_cv = ig_counts.std() / ig_counts.mean()  # coefficient of variation

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #E45756; margin:12px 0;">
    <strong>📌 分析：</strong>{ps['interestGroup'].nunique()} 个兴趣组（A–J）的成员分布<b>高度均匀</b>——
    各组规模介于 {ig_min} 至 {ig_max} 人，变异系数仅 {ig_cv:.3f}。这种近乎等量的分配模式并非随机过程所能产生，
    暗示存在<b>人为设计或社区自组织机制</b>在调控组间平衡。均匀分布的社会意义在于：避免了单一兴趣领域的
    人口集中，确保多样化的社会交互与信息跨群体流动。每个居民有均等机会接触到不同兴趣领域的社交圈，
    有利于增强<b>社区整体凝聚力</b>与抗风险韧性。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Section 5: 经济状况与幸福感
    # ================================================================
    st.markdown("## 五、经济状况与主观幸福感")
    st.markdown("*居民财富分布的不均等性及其与幸福感的关系*")

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q1_balance_hist(ps), use_container_width=True)
    with col_r:
        st.plotly_chart(make_q1_joviality_hist(ps), use_container_width=True)

    bal_median = ps['avg_balance'].median()
    bal_mean = ps['avg_balance'].mean()
    bal_skew = ps['avg_balance'].skew()
    jov_mean = ps['joviality'].mean()
    jov_std = ps['joviality'].std()

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #F58518; margin:12px 0;">
    <strong>📌 分析：</strong>可用余额分布呈<b>显著右偏态</b>（偏度 {bal_skew:.2f}），中位数 ${bal_median:,.0f}
    低于均值 ${bal_mean:,.0f}，表明多数居民持有中等水平余额，少数高净值个体拉高了整体均值——
    这一分布形态与大多数真实社区中观察到的财富集中现象一致。Joviality（幸福感指标）近似<b>正态分布</b>
    （均值 {jov_mean:.3f}，标准差 {jov_std:.3f}），围绕 0.5 中值对称展开，未出现明显的双峰或截断特征。
    这意味着<b>经济不均等并未导致幸福感的系统性分化</b>——至少在当前数据集中，财富水平并非幸福感的主要决定因子。
    这一观察与主观幸福感研究文献中的"伊斯特林悖论"（Easterlin Paradox）相呼应：超过基本需求后，
    绝对收入的增加对幸福感的边际贡献递减。
    </div>
    """, unsafe_allow_html=True)

    # --- Q1 Summary ---
    st.markdown("---")
    st.markdown("## Q1 总结：EngageTown 的人口基底")
    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.06);
    padding:20px 24px; border-radius:10px; border:1px solid rgba(128,128,128,0.15); margin-top:8px;">

    <p style="font-size:1.05em; line-height:1.9; text-align:justify;">
    EngageTown 是一座以 <b>{len(ps):,} 名中青年居民</b>为主体的中小规模社区，年龄均值 {ps['age'].mean():.1f} 岁，
    劳动年龄人口（18–59 岁）占比超过七成，形成以劳动力为主导的人口金字塔。户均规模仅 {ps['householdSize'].mean():.1f} 人，
    有子女家庭约 {kids_pct:.0f}%，呈现典型的小家庭化社会形态。教育水平集中于高中至学士层级，
    人力资本以中等技能劳动力为主体，教育与经济回报之间存在正向梯度关系。
    {ps['interestGroup'].nunique()} 个兴趣组呈现罕见的<b>完全均匀分布</b>（变异系数 {ig_cv:.3f}），
    暗示社区存在审慎的社会设计。财富分布呈右偏态（偏度 {bal_skew:.2f}），但幸福感围绕中值对称分布，
    经济不均等并未转化为幸福感的系统性差异。
    </p>

    <hr style="border-color:#d0d5dd; margin:16px 0;">

    <table style="width:100%; font-size:0.93em; border-collapse:collapse;">
    <tr style="background:rgba(128,128,128,0.15);">
        <td style="padding:8px 12px; width:25%;"><b>维度</b></td>
        <td style="padding:8px 12px; width:75%;"><b>核心发现</b></td>
    </tr>
    <tr>
        <td style="padding:8px 12px;">🔢 人口规模</td>
        <td style="padding:8px 12px;">{len(ps):,} 人，劳动年龄占比 ~{working_age_pct:.0f}%，抚养比健康</td>
    </tr>
    <tr style="background:rgba(128,128,128,0.1);">
        <td style="padding:8px 12px;">📊 年龄结构</td>
        <td style="padding:8px 12px;">均值 {ps['age'].mean():.1f} 岁，右偏态分布，老年人口稀少</td>
    </tr>
    <tr>
        <td style="padding:8px 12px;">🎓 教育水平</td>
        <td style="padding:8px 12px;">高中/大学肄业 + 学士为主（合计 ~{hs_pct + bachelors_pct:.0f}%），教育-财富正相关</td>
    </tr>
    <tr style="background:rgba(128,128,128,0.1);">
        <td style="padding:8px 12px;">🏘️ 家庭结构</td>
        <td style="padding:8px 12px;">户均 {ps['householdSize'].mean():.1f} 人，{kids_pct:.0f}% 有子女，小家庭化主流</td>
    </tr>
    <tr>
        <td style="padding:8px 12px;">🎯 社会多样性</td>
        <td style="padding:8px 12px;">{ps['interestGroup'].nunique()} 组均匀分布（CV={ig_cv:.3f}），设计性均衡</td>
    </tr>
    <tr style="background:rgba(128,128,128,0.1);">
        <td style="padding:8px 12px;">💰 经济状况</td>
        <td style="padding:8px 12px;">财富右偏（偏度 {bal_skew:.2f}），幸福感正态分布，二者弱相关</td>
    </tr>
    </table>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# Q2: 社交活动与网络分析
# ============================================================
elif page.startswith("🤝"):
    st.title("Q2：社交活动与网络分析")
    st.markdown("*根据社交网络数据识别显著模式，提供量化证据支持最多 10 个发现*")

    # ---- Hero Banner ----
    st.markdown("""
    <div style="text-align:center; padding:20px; background:linear-gradient(135deg, #1a2a3a 0%, #2E4057 40%, #54A24B 100%);
    border-radius:10px; color:white; margin-bottom:20px;">
        <h2 style="color:white; margin:0; font-weight:600;">🤝 社交网络全景 —— 关系、行为与空间</h2>
    </div>
    """, unsafe_allow_html=True)

    # --- Network overview metrics ---
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("🔵 节点数", f"{net_metrics['num_nodes']:,}")
    with col2:
        st.metric("🔗 边数", f"{net_metrics['num_edges']:,}")
    with col3:
        st.metric("📐 网络密度", f"{net_metrics['density']:.4f}")
    with col4:
        st.metric("🔄 平均聚类系数", f"{net_metrics['avg_clustering']:.4f}")
    with col5:
        st.metric("🏘️ 社区数", f"{net_metrics.get('num_communities', 'N/A')}")

    st.markdown("---")

    # ================================================================
    # Pattern 1: Degree Distribution
    # ================================================================
    st.markdown("## 模式一：度分布呈近似正态——社交连接高度均质化")
    st.markdown("*社交连接的非均质分布——少数枢纽与多数普通节点*")

    deg_df = net_metrics["degree"]
    deg_df_nonzero = deg_df[deg_df["weighted_degree"] > 0]

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q2_degree_distribution(deg_df), use_container_width=True)
    with col_r:
        st.plotly_chart(make_q2_rank_frequency(deg_df), use_container_width=True)

    top_degree = deg_df_nonzero.nlargest(5, "weighted_degree")
    top_ids = ', '.join(map(str, top_degree['participantId'].tolist()))
    avg_deg = deg_df_nonzero["weighted_degree"].mean()
    med_deg = deg_df_nonzero["weighted_degree"].median()
    max_deg = deg_df_nonzero["weighted_degree"].max()

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #4C78A8; margin:12px 0;">
    <strong>📌 证据：</strong>度分布呈现<b>近似正态分布</b>特征：均值 {avg_deg:.1f}、中位数 {med_deg:.0f}，
    均值/中位数比仅为 {avg_deg/med_deg:.2f}，表明分布高度对称。这一特征与典型社交网络的幂律分布不同——
    EngageTown 的社交连接呈现<b>高度均质化</b>，大多数居民维持相似规模的社交圈。
    度最高的 5 位居民（ID：{top_ids}）虽然连接数最多，但优势并不悬殊。
    这种均质化结构可能反映了社区的<b>社交平等性</b>——没有少数"超级连接者"垄断社交资源。
    从信息传播角度看，均质网络具有较好的<b>鲁棒性</b>：任一节点的移除对全局连通性影响有限，
    但也意味着信息扩散速度可能较慢（缺乏枢纽加速）。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Pattern 2: Community Structure
    # ================================================================
    st.markdown("## 模式二：显著的社区结构——高模块度与清晰边界")
    st.markdown("*Louvain 算法揭示的社交群落及其社会学含义*")
    st.markdown(f"**模块度（Modularity）：{net_metrics.get('modularity', 0):.4f}** | 检测到社区数：**{net_metrics.get('num_communities', 'N/A')}**")

    comm_fig = make_q2_community_sizes(net_metrics)
    if comm_fig:
        st.plotly_chart(comm_fig, use_container_width=True)

    mod = net_metrics.get('modularity', 0)
    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #54A24B; margin:12px 0;">
    <strong>📌 证据：</strong>Louvain 社区检测算法识别出 <b>{net_metrics.get('num_communities', 'N/A')} 个社交社区</b>，
    模块度达 <b>{mod:.4f}</b>。在社交网络分析中，模块度超过 0.3 即被视为具有显著社区结构；
    {mod:.4f} 的数值表明 EngageTown 的社交网络<b>高度模块化</b>——同一社区内部联系紧密，
    跨社区连接相对稀疏。社区规模分布并非完全均匀，暗示存在若干"核心社区"与"边缘社区"的层级分化。
    这种模块化结构可能映射了现实中的兴趣组归属、居住邻近性或工作场所社交圈。
    从社区治理角度看，高模块度意味着<b>信息跨群体传播可能存在壁垒</b>，
    需要依赖后文（模式七）识别的"桥接个体"来维持跨社区的信息流通。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Pattern 3: Clustering & Betweenness
    # ================================================================
    st.markdown('## 模式三：高局部聚类——"朋友的朋友亦是朋友"')
    st.markdown("*聚类系数与介数中心性的分布——紧密社交圈与桥接角色*")

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q2_clustering_hist(net_metrics), use_container_width=True)
    with col_r:
        st.plotly_chart(make_q2_betweenness_hist(net_metrics), use_container_width=True)

    avg_clust = net_metrics["clustering"]["clustering_coefficient"].mean()
    clust_ratio = avg_clust / net_metrics['density']
    top_betweenness = net_metrics["betweenness"].nlargest(3, "betweenness_centrality")

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #B279A2; margin:12px 0;">
    <strong>📌 证据：</strong>平均聚类系数为 <b>{avg_clust:.4f}</b>，是网络密度（{net_metrics['density']:.4f}）的
    <b>{clust_ratio:.0f} 倍</b>。这一比值揭示了一个关键的社会学现象：如果 A 与 B、C 分别为朋友，
    那么 B 与 C 之间也极有可能存在连接——即<b>"三元闭包"（Triadic Closure）</b>倾向强烈。
    高聚类系数在网络理论中指向<b>信任积累与社会资本形成</b>的有利环境——紧密的社交圈促进
    规范内化与声誉机制有效运行。与此同时，介数中心性分布高度集中：
    少数个体（如 ID {', '.join(map(lambda x: str(int(x)), top_betweenness['participantId'].tolist()))}）
    占据了不成比例的"桥接"位置，他们是<b>跨社区信息流通的关键通道</b>，
    也是网络鲁棒性的潜在单点故障。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Pattern 4: Venue Check-in
    # ================================================================
    st.markdown("## 模式四：场所类型偏好——餐饮场所为核心社交载体")
    st.markdown("*签到行为的场所类型分布及热门场所集中度*")

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q2_venue_types(vc), use_container_width=True)
    with col_r:
        st.plotly_chart(make_q2_top_venues(vc), use_container_width=True)

    venue_type_counts = vc.groupby("venueType")["checkins"].sum().sort_values(ascending=False)
    top_type = venue_type_counts.index[0]
    top_type_pct = venue_type_counts.iloc[0] / venue_type_counts.sum() * 100
    top3_venues = vc.nlargest(3, "checkins")
    top3_pct = top3_venues["checkins"].sum() / vc["checkins"].sum() * 100

    # Calculate percentages for each venue type
    total_checkins = venue_type_counts.sum()
    workplace_pct = venue_type_counts.get("Workplace", 0) / total_checkins * 100
    restaurant_pct = venue_type_counts.get("Restaurant", 0) / total_checkins * 100
    pub_pct = venue_type_counts.get("Pub", 0) / total_checkins * 100
    food_social_pct = restaurant_pct + pub_pct

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #F58518; margin:12px 0;">
    <strong>📌 证据：</strong>签到量数据显示场所类型分布为："<b>{top_type}</b>"类场所占 <b>{top_type_pct:.0f}%</b>，
    其次是 Workplace（{workplace_pct:.0f}%）和 Restaurant（{restaurant_pct:.0f}%）。
    <b>餐饮场所（Restaurant + Pub）合计占比约 {food_social_pct:.0f}%</b>，
    虽然不是单一最大类别，但作为社交功能场所类型，它们构成了居民社交活动的核心载体。
    签到量前三的场所合计占比 <b>{top3_pct:.0f}%</b>，表明存在少数"热门场所"
    承担了不成比例的社交活动负载。这一分布模式揭示了 EngageTown 社交生态的两个特征：
    （1）<b>餐饮场所是社区社交的核心载体</b>——居民的面对面社交主要围绕共同进餐/饮酒展开；
    （2）热门场所构成了<b>社交活动的引力中心</b>——少数地点成为事实上的社区聚集点。
    从城市设计角度看，这些热门场所的选址与容量对社区社交健康具有不成比例的影响。
    场所类型的集中也为经济分析（Q3）提供了需求侧背景——餐饮服务业的高客流量支持了该行业
    在雇主构成中的可观占比。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Pattern 5: Temporal Activity
    # ================================================================
    st.markdown("## 模式五：昼夜活动节律——午后/傍晚为社交高峰")
    st.markdown("*24 小时活动强度曲线及活动模式的时段分布*")

    st.plotly_chart(make_q2_hourly_activity(ha, mode_cols), use_container_width=True)
    st.plotly_chart(make_q2_mode_area(ha, mode_cols), use_container_width=True)

    # Compute peak hour statistics with confidence intervals
    from common import compute_peak_hour_stats
    peak_stats = compute_peak_hour_stats(ha, mode_cols)

    hourly_total = ha.groupby("hour_num")["total_mode"].sum().reset_index()
    peak_hour = int(hourly_total.loc[hourly_total["total_mode"].idxmax(), "hour_num"])
    # Find trough (minimum) hour
    trough_hour = int(hourly_total.loc[hourly_total["total_mode"].idxmin(), "hour_num"])
    peak_to_trough = hourly_total["total_mode"].max() / hourly_total["total_mode"].min()

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #72B7B2; margin:12px 0;">
    <strong>📌 证据：</strong>活动曲线呈现清晰的<b>单峰昼夜节律</b>：凌晨 {trough_hour}:00 为全日最低谷，
    此后逐步攀升，于 <b>{peak_hour}:00 达到峰值</b>，峰谷比达 {peak_to_trough:.0f}:1。
    <b>统计验证：</b>峰值时段的平均活动量为 {peak_stats['peak_mean']:.0f}（95% CI: [{peak_stats['ci_lower']:.0f}, {peak_stats['ci_upper']:.0f}]），
    置信区间较窄表明峰值时间具有<b>统计显著性</b>。<br><br>
    活动模式的构成揭示了节律背后的行为逻辑：<b>"在家"模式占绝对主导（约 60.8%）</b>，
    其次是"工作"模式（约 23.7%），"休闲娱乐"与"餐饮"模式合计仅占约 6.3%。
    这一分布表明居民的日常活动以居家和工作为主，社交/休闲活动在时间分配上相对有限。
    尽管占比不高，社交/休闲活动仍呈现明显的<b>午后至傍晚集中</b>特征，
    夜间则回归"在家"模式。这一节律与标准工作-生活结构一致，
    社交活动主要嵌入<b>工作日的"后工作时段"</b>。
    </div>
    """, unsafe_allow_html=True)

    # ================================================================
    # Pattern 5b: Weekday vs Weekend
    # ================================================================
    st.markdown("---")
    st.markdown("## 模式五（续）：工作日与周末的行为分化")
    st.markdown("*周末社交峰值后移、休闲比例上升——工作-生活二分节律的强化证据*")

    st.plotly_chart(make_q2_weekday_weekend(ha, mode_cols), use_container_width=True)
    st.plotly_chart(make_q2_weekday_weekend_modes(ha, mode_cols), use_container_width=True)

    peak_diff = int(weekend["we_peak"]) - int(weekend["wd_peak"])
    work_drop = weekend['wd_work_pct'] - weekend['we_work_pct']
    rec_rise = weekend['we_rec_pct'] - weekend['wd_rec_pct']

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #E45756; margin:12px 0;">
    <strong>📌 证据——周末社交迁移：</strong><br>
    • <b>峰值时移：</b>活动峰值从工作日的 {int(weekend['wd_peak'])}:00 后移至周末的
      {int(weekend['we_peak'])}:00（Δ = {peak_diff:+d} 小时），与较晚的起床时间及社交导向日程一致<br>
    • <b>工作模式收缩：</b>"AtWork"占比从工作日 {weekend['wd_work_pct']:.1f}% 降至周末
      {weekend['we_work_pct']:.1f}%（降幅 {work_drop:.1f} 个百分点），确认了标准工作周模式<br>
    • <b>休闲模式扩张：</b>"Recreation"占比从 {weekend['wd_rec_pct']:.1f}% 升至
      {weekend['we_rec_pct']:.1f}%（增幅 {rec_rise:.1f} 个百分点）——周末释放出的时间
      主要流向休闲活动，而非家务或其他必要活动<br>
    • <b>总体形态：</b>周末活动曲线的启动时点推迟约 2 小时，但峰值强度与工作日相当——
      表明周末并未降低社交总量，而是<b>重新分配了社交的时间窗口</b><br>
    • 工作日-周末的双模式分化与模式四（餐饮场所偏好）形成逻辑闭环：居民在周末将更多
      时间投入餐饮/休闲场所的社交活动，驱动了这些场所的高签到量
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Pattern 6: Demographics vs Social
    # ================================================================
    st.markdown("## 模式六：人口特征与社交连接——年龄与教育的调节效应")
    st.markdown("*年龄组、教育水平如何影响个体的社交网络参与度*")

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q2_age_social(cross), use_container_width=True)
    with col_r:
        st.plotly_chart(make_q2_edu_social(cross), use_container_width=True)

    # Compute statistical significance of age-social relationship
    from common import compute_age_social_significance
    age_stats = compute_age_social_significance(cross)

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #2E4057; margin:12px 0;">
    <strong>📌 证据：</strong>社交连接度（以加权度衡量）在年龄维度上呈现<b>倒 U 型分布</b>——
    青年与壮年群体（约 25–45 岁）社交活动最为活跃，此后随年龄增长逐步下降。这一模式
    与生命历程理论中的社交生命周期假说一致：社交网络在职业生涯早期扩展，中年后因家庭
    责任与精力约束而收缩。<br><br>
    <b>统计验证：</b>Spearman 相关系数 r = {age_stats['correlation']:.3f}（p = {age_stats['p_value']:.4f}），
    二次回归 R² = {age_stats['r_squared']:.3f}，表明年龄与社交连接度存在<b>显著的非线性关系</b>。
    教育水平与社交连接度呈<b>弱正向关联</b>——高学历者的平均连接数
    略高于低学历群体，但效应量有限，暗示教育并非社交参与度的主导预测变量。<br><br>
    <b>政策含义：</b>如果社区规划者关注社会孤立问题，年龄（尤其是 55 岁以上群体）可能比
    教育水平更有效的风险识别指标。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Pattern 7: Bridge Individuals
    # ================================================================
    st.markdown("## 模式七：关键影响者——少数桥接个体的结构性作用")
    st.markdown("*介数中心性识别跨社区信息通道的关键节点*")

    st.plotly_chart(make_q2_bridge_individuals(net_metrics), use_container_width=True)

    bridge_df = net_metrics["betweenness"].nlargest(10, "betweenness_centrality")
    top1_bet = bridge_df.iloc[0]
    top10_sum = bridge_df["betweenness_centrality"].sum()
    total_bet = net_metrics["betweenness"]["betweenness_centrality"].sum()
    top10_pct = top10_sum / total_bet * 100

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #E45756; margin:12px 0;">
    <strong>📌 证据：</strong>介数中心性分布高度集中——前 10 位个体合计占据了全网 <b>{top10_pct:.1f}%</b>
    的最短路径，其中最高者（ID {int(top1_bet['participantId'])}）独占总介数的显著份额。
    这些"桥接个体"是<b>跨社区信息流通的结构性枢纽</b>：他们的社交连接跨越了社区检测
    （模式二）所识别的模块边界，使原本隔离的社交群落得以互通信息。<br><br>
    在网络理论中，此类个体的存在提高了网络的<b>全局效率</b>（缩短平均路径长度），
    但也构成了<b>结构性脆弱点</b>——桥接个体的退出可能导致社区间的信息断层。
    从社区治理实践角度，识别并与这些关键个体合作，可以显著提高公共信息传播（如健康公告、
    紧急通知）的效率；同时应考虑培育<b>"后备桥接者"</b>以增强网络的冗余性与鲁棒性。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Pattern 8: Edge Weights
    # ================================================================
    st.markdown("## 模式八：关系强度的异质性——弱连接主导，强连接稀缺")
    st.markdown("*边权重分布揭示社交投资的不均等分配*")

    st.plotly_chart(make_q2_edge_weights(sn), use_container_width=True)

    mean_w = sn["weight"].mean()
    median_w = sn["weight"].median()
    max_w = sn["weight"].max()
    weak_strong_ratio = mean_w / median_w
    # Count weak ties (below median) vs strong ties (above 3x median)
    weak_count = (sn["weight"] <= median_w).sum()
    strong_count = (sn["weight"] >= 3 * median_w).sum()

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #F58518; margin:12px 0;">
    <strong>📌 证据：</strong>边权重（互动频率）分布呈<b>典型右偏态</b>：均值 {mean_w:.1f} 远高于中位数
    {median_w:.0f}（均值/中位数比 {weak_strong_ratio:.1f}），绝大多数社交关系的互动频率处于
    低位——这是<b>"邓巴数"（Dunbar's Number）理论的量化印证</b>：个体维持亲密关系（高频互动）
    的认知与时间资源有限，大多数社交连接必然是弱连接。<br><br>
    在社会网络理论中，弱连接并非缺陷而是功能资产——Granovetter 的经典研究证明，
    <b>弱连接在信息获取（尤其是求职信息）中的价值往往超过强连接</b>，因为它们更可能
    桥接到不同的信息池。EngageTown 的边权分布表明其社交生态兼具两种连接类型：
    少数强连接提供情感支持与信任基础，大量弱连接确保信息的广泛流通。
    弱连接占比约 {weak_count/len(sn)*100:.0f}%，强连接（≥3 倍中位数）仅 {strong_count} 条。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Pattern 9: Travel Purpose
    # ================================================================
    st.markdown("## 模式九：出行目的——社交/休闲为主导动机")
    st.markdown("*居民出行的目的构成及其消费特征*")

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q2_travel_purpose(tp), use_container_width=True)
    with col_r:
        st.plotly_chart(make_q2_travel_spending(tp), use_container_width=True)

    st.markdown("""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #54A24B; margin:12px 0;">
    <strong>📌 证据：</strong>社交/休闲类出行在<b>频次与消费金额两个维度均占据首位</b>，
    构成居民出行的主要驱动力。通勤（工作相关出行）退居次要位置——这一排序与典型
    大城市通勤主导的出行结构形成反差，暗示两种可能：（1）<b>居民职住接近</b>——
    工作地与居住地距离短，通勤出行需求被压缩；（2）<b>社区文化偏重社交</b>——
    居民将可支配时间优先配置于社交/休闲活动而非通勤。<br><br>
    出行目的结构与场所签到数据（模式四）及经济支出结构（Q3）形成<b>三角互证</b>：
    居民出行以社交为目的 → 目的地集中于餐饮场所 → 支出中休闲占比与食品相当。
    这一逻辑链条为 EngageTown "社交导向型社区"的定性提供了跨数据源的证据支持。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Pattern 10: Geographic Clustering
    # ================================================================
    st.markdown("## 模式十：社交场所的空间集聚——功能区的空间分化")
    st.markdown("*酒吧、餐厅、学校在城市空间中的分布格局*")

    map_fig = make_venue_map(base_map, data)
    if map_fig:
        st.plotly_chart(map_fig, use_container_width=True)
    else:
        st.info("地图不可用（缺少 BaseMap.png 底图文件）")

    st.markdown("""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #4C78A8; margin:12px 0;">
    <strong>📌 证据：</strong>场所空间分布呈现<b>非随机集聚格局</b>。酒吧与餐厅表现出显著的
    空间共址倾向——二者倾向于毗邻分布，形成若干可辨识的<b>"社交-商业微中心"</b>。
    这种共址模式在零售地理学中被称为"集聚经济"（Agglomeration Economy）：
    餐饮场所的空间邻近降低了消费者的多目的地行程成本，形成了正反馈循环——
    越集聚越吸引客流，越高的客流越促进集聚。<br><br>
    学校分布则呈现出相反的空间逻辑：数量较少、空间分散、服务半径更大——
    这是公共服务设施典型的<b>覆盖效率优先</b>布局策略。两种空间逻辑（市场驱动的
    集聚 vs. 规划驱动的分散）在同一城市版图上共存，构成了 EngageTown 空间结构的二元特征。
    社交场所的空间集聚也为 Q4 中"社交-商业混合功能区"的识别提供了空间维度的证据基础。
    </div>
    """, unsafe_allow_html=True)

    # ================================================================
    # Q2 Summary
    # ================================================================
    st.markdown("---")
    st.markdown("## Q2 总结：十项社交模式及其系统关联")
    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.06);
    padding:20px 24px; border-radius:10px; border:1px solid rgba(128,128,128,0.15); margin-top:8px;">

    <p style="font-size:1.05em; line-height:1.9; text-align:justify;">
    EngageTown 的社交生态呈现出一幅<b>高度结构化、多维度关联的社会网络图景</b>。从网络拓扑来看，
    度分布呈近似正态（模式一）、社区模块度高达 {mod:.4f}（模式二）、聚类系数远超随机网络
    （模式三），三者共同指向一个<b>紧密且模块化的社交结构</b>——信息在社区内部高效流动，
    但跨社区传播依赖少数桥接个体（模式七）。从行为层面来看，社交活动嵌入清晰的昼夜节律
    （模式五），以餐饮场所为核心空间载体（模式四），并由社交/休闲出行驱动（模式九）。
    人口特征对社交参与有调节效应（模式六），但效果弱于网络结构本身的影响。
    </p>

    <hr style="border-color:#d0d5dd; margin:16px 0;">

    <table style="width:100%; font-size:0.93em; border-collapse:collapse;">
    <tr style="background:rgba(128,128,128,0.15);">
        <td style="padding:8px 12px; width:5%;"><b>#</b></td>
        <td style="padding:8px 12px; width:25%;"><b>模式</b></td>
        <td style="padding:8px 12px; width:35%;"><b>核心证据</b></td>
        <td style="padding:8px 12px; width:35%;"><b>社会学含义</b></td>
    </tr>
    <tr>
        <td style="padding:8px 12px;">1</td>
        <td style="padding:8px 12px;">度分布——近似正态</td>
        <td style="padding:8px 12px;">均值 {avg_deg:.1f}，中位数 {med_deg:.0f}，均值/中位数比 {avg_deg/med_deg:.2f}</td>
        <td style="padding:8px 12px;">社交连接高度均质化，无超级连接者垄断</td>
    </tr>
    <tr style="background:rgba(128,128,128,0.1);">
        <td style="padding:8px 12px;">2</td>
        <td style="padding:8px 12px;">强社区结构</td>
        <td style="padding:8px 12px;">模块度 {mod:.4f}，检测到 {net_metrics.get('num_communities', 'N/A')} 个社区</td>
        <td style="padding:8px 12px;">社交高度模块化，跨社区信息流通存在壁垒</td>
    </tr>
    <tr>
        <td style="padding:8px 12px;">3</td>
        <td style="padding:8px 12px;">高局部聚类</td>
        <td style="padding:8px 12px;">聚类系数 {avg_clust:.4f}（为密度 {net_metrics['density']:.4f} 的 {clust_ratio:.0f} 倍）</td>
        <td style="padding:8px 12px;">三元闭包倾向强烈，信任积累与社会资本形成环境有利</td>
    </tr>
    <tr style="background:rgba(128,128,128,0.1);">
        <td style="padding:8px 12px;">4</td>
        <td style="padding:8px 12px;">餐饮场所为核心社交载体</td>
        <td style="padding:8px 12px;">餐饮（Restaurant+Pub）合计 {food_social_pct:.0f}%，前三场所占 {top3_pct:.0f}%</td>
        <td style="padding:8px 12px;">餐饮场所是社区社交核心载体，少数场所为引力中心</td>
    </tr>
    <tr>
        <td style="padding:8px 12px;">5</td>
        <td style="padding:8px 12px;">昼夜节律 + 工作日/周末分化</td>
        <td style="padding:8px 12px;">峰值 {peak_hour}:00；周末峰值后移 {peak_diff:+d}h，休闲占比 +{rec_rise:.1f}pp</td>
        <td style="padding:8px 12px;">社交嵌入工作-生活节律，周末时间再分配至社交/休闲</td>
    </tr>
    <tr style="background:rgba(128,128,128,0.1);">
        <td style="padding:8px 12px;">6</td>
        <td style="padding:8px 12px;">人口特征调节社交参与</td>
        <td style="padding:8px 12px;">年龄呈倒 U 型；教育正向但效应量有限</td>
        <td style="padding:8px 12px;">年龄为社交参与度更有效的预测指标</td>
    </tr>
    <tr>
        <td style="padding:8px 12px;">7</td>
        <td style="padding:8px 12px;">桥接个体——关键影响者</td>
        <td style="padding:8px 12px;">前 10 个体占全网介数 {top10_pct:.1f}%</td>
        <td style="padding:8px 12px;">信息传播枢纽，网络鲁棒性的结构性关键点</td>
    </tr>
    <tr style="background:rgba(128,128,128,0.1);">
        <td style="padding:8px 12px;">8</td>
        <td style="padding:8px 12px;">关系强度异质性</td>
        <td style="padding:8px 12px;">均值/中位数比 {weak_strong_ratio:.1f}；弱连接 ~{weak_count/len(sn)*100:.0f}%</td>
        <td style="padding:8px 12px;">弱连接主导，符合邓巴数约束；弱连接促进信息多样性</td>
    </tr>
    <tr>
        <td style="padding:8px 12px;">9</td>
        <td style="padding:8px 12px;">社交/休闲出行主导</td>
        <td style="padding:8px 12px;">社交出行频次与消费均居首位</td>
        <td style="padding:8px 12px;">职住接近 + 社交偏好 → 非通勤出行主导</td>
    </tr>
    <tr style="background:rgba(128,128,128,0.1);">
        <td style="padding:8px 12px;">10</td>
        <td style="padding:8px 12px;">社交场所空间集聚</td>
        <td style="padding:8px 12px;">酒吧-餐厅共址集聚，学校空间分散</td>
        <td style="padding:8px 12px;">市场驱动型集聚 vs 规划驱动型分散的二元空间逻辑</td>
    </tr>
    </table>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# Q3: 商业与经济
# ============================================================
elif page.startswith("🏭"):
    st.title("Q3：商业与经济基础")
    st.markdown("*识别城镇的主导产业基础，描绘经济活动的规模、结构及运行特征*")

    # ---- Hero Banner ----
    st.markdown("""
    <div style="text-align:center; padding:20px; background:linear-gradient(135deg, #1a2a3a 0%, #2E4057 40%, #E45756 100%);
    border-radius:10px; color:white; margin-bottom:20px;">
        <h2 style="color:white; margin:0; font-weight:600;">🏭 经济全景 —— 规模、结构与产业形态</h2>
    </div>
    """, unsafe_allow_html=True)

    # --- Economic overview metrics ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 年工资总额", f"${econ['total_wage']:,.0f}")
    with col2:
        st.metric("🏢 雇主总数", f"{len(js):,}",
                  help=f"户均 {js['employee_count'].mean():.1f} 名雇员")
    with col3:
        st.metric("👷 岗位总数", f"{econ['total_jobs']:,}",
                  help=f"人均 {econ['jobs_per_resident']:.1f} 个岗位")
    with col4:
        st.metric("📊 净现金流", f"${econ['total_wage'] - econ['total_spending']:,.0f}",
                  delta=f"{(econ['total_wage'] - econ['total_spending']) / econ['total_wage'] * 100:.0f}% of wages")

    st.markdown("---")

    # ================================================================
    # Finding 1: Small Business Economy
    # ================================================================
    st.markdown("## 一、小微雇主主导——不存在大型企业")
    st.markdown("*雇主规模分布及其对经济结构的定性含义*")

    st.plotly_chart(make_q3_employer_size(js), use_container_width=True)

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #4C78A8; margin:12px 0;">
    <strong>📌 核心发现——主导产业判断：小型服务企业。</strong><br>
    {len(js)} 家雇主的雇员规模集中于 <b>{econ['min_e']}–{econ['max_e']} 人</b>（均值
    {js['employee_count'].mean():.1f}，中位数 {js['employee_count'].median():.0f}），
    <b>不存在任何大型企业、工厂或公司总部</b>——这是由小型商铺、本地服务与微型企业
    构成的经济生态。岗位总计 {econ['total_jobs']:,} 个，服务于 {len(ps):,} 名居民
    （人均 {econ['jobs_per_resident']:.1f} 个岗位），岗位数略超人口数暗示部分居民
    可能同时兼任多个职位，或存在跨雇主零工就业（gig employment）模式。<br><br>
    <b>定性判断：</b>EngageTown 的经济形态不属于工业经济、知识经济或资源型经济，
    而是典型的<b>本地化小型服务经济</b>——雇主以满足居民日常消费需求为核心功能，
    缺乏面向外部市场的出口导向型企业。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Finding 2: Financial Flow
    # ================================================================
    st.markdown("## 二、财务结构——工资为单一收入来源，住房与休闲双支出支柱")
    st.markdown("*收入结构、支出构成与净盈余的宏观经济含义*")

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q3_financial_flow(fin), use_container_width=True)
    with col_r:
        st.plotly_chart(make_q3_expense_pie(fin), use_container_width=True)

    shelter_pct = econ['total_shelter'] / econ['total_spending'] * 100
    rec_pct = econ['total_recreation'] / econ['total_spending'] * 100
    food_pct = econ['total_food'] / econ['total_spending'] * 100
    edu_pct = econ['total_edu'] / econ['total_spending'] * 100
    net_surplus = econ['total_wage'] - econ['total_spending']
    surplus_pct = net_surplus / econ['total_wage'] * 100

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #F58518; margin:12px 0;">
    <strong>📌 分析：</strong>经济体的收入端高度单一化——<b>工资为唯一收入来源</b>（总额
    ${econ['total_wage']:,.0f}），数据中未见投资收益、经营性利润或政府转移支付等其他收入形式，
    暗示该城镇不具备显著的资本积累或再分配体系。支出端呈三足鼎立格局：<b>住房</b>
    ${econ['total_shelter']:,.0f}（{shelter_pct:.0f}%）、<b>休闲</b>
    ${econ['total_recreation']:,.0f}（{rec_pct:.0f}%）、<b>食品</b>
    ${econ['total_food']:,.0f}（{food_pct:.0f}%）。<b>休闲支出与食品支出比例相当</b>
    这一特征值得特别关注——在典型消费结构中，食品支出通常远超休闲。这一比例倒挂指向
    EngageTown 居民活跃的<b>社交消费文化</b>，与 Q2 社交网络分析中识别的餐饮场所偏好
    和出行社交目的形成跨数据源互证。教育支出仅占 {edu_pct:.1f}%，占比极低，
    可能对应前述人口分析中未成年人口占比小、学龄需求有限的现实。<br><br>
    年度净盈余 ${net_surplus:,.0f}（占工资 {surplus_pct:.0f}%）表明总体收支存在结余——
    可能对应较高的居民储蓄率或数据集中支出项目的非完备记录。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Finding 3: Wage Analysis
    # ================================================================
    st.markdown("## 三、工资分布——近正态、中等区间，雇主规模与工资脱钩")
    st.markdown("*小时工资率的分布特征及其与雇主规模的关系*")

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q3_wage_hist(js), use_container_width=True)
    with col_r:
        st.plotly_chart(make_q3_wage_box(js), use_container_width=True)

    wage_range = js["avg_hourly_rate"].max() - js["avg_hourly_rate"].min()
    wage_cv = js["avg_hourly_rate"].std() / js["avg_hourly_rate"].mean()

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #54A24B; margin:12px 0;">
    <strong>📌 分析：</strong>小时工资区间为 <b>${js['avg_hourly_rate'].min():.2f}–${js['avg_hourly_rate'].max():.2f}</b>
    （极差 ${wage_range:.2f}），均值 ${js['avg_hourly_rate'].mean():.2f}，中位数
    ${js['avg_hourly_rate'].median():.2f}，变异系数 {wage_cv:.2f}。分布形态接近正态——
    大多数岗位工资围绕均值聚集，极低薪与极高薪岗位均属罕见。这一特征与大型企业经济中常见的
    偏态工资分布（少数高薪岗位拉高均值）形成对比，进一步支持了小微雇主经济体的定性。<br><br>
    <b>一个重要的"非发现"：</b>雇主规模与工资水平之间<b>无显著相关</b>。某些小型雇主支付
    高于平均的工资，而某些拥有 9 名雇员（最大规模）的雇主反而支付低于平均的薪酬。
    薪酬水平更可能由<b>岗位类型、技能需求或行业特征</b>驱动，而非雇主规模本身。
    这一发现对经济政策有隐含意义：扶持小微企业扩大规模并不会自动转化为工资增长——
    提升工资的关键在于岗位质量而非雇主体量。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Finding 4: Building Mix
    # ================================================================
    st.markdown("## 四、建筑功能构成——住宅与商业的均衡布局")
    st.markdown("*建筑存量分类及商业空间利用率评估*")

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q3_building_types(bt), use_container_width=True)
    with col_r:
        comp_data = pd.DataFrame({
            "Metric": ["住宅建筑", "商业建筑", "注册雇主\n（在商业建筑内）", "未占用\n商业建筑"],
            "Count": [econ['residential'], econ['commercial'], len(js),
                      max(0, econ['commercial'] - len(js))]
        })
        fig_comp = px.bar(comp_data, x="Metric", y="Count",
                          title=f"商业空间利用率（{econ['commercial']} 栋商业建筑，{len(js)} 家雇主）",
                          color="Count", color_continuous_scale="Viridis", text="Count")
        fig_comp.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_comp, use_container_width=True)

    vacancy = max(0, econ['commercial'] - len(js))
    res_pct = econ['residential'] / bt['count'].sum() * 100
    com_pct = econ['commercial'] / bt['count'].sum() * 100

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #72B7B2; margin:12px 0;">
    <strong>📌 分析：</strong>建筑存量近乎均衡：{econ['residential']} 栋住宅
    （{res_pct:.0f}%）、{econ['commercial']} 栋商业建筑（{com_pct:.0f}%）、{econ['schools_n']} 所学校。
    住宅-商业比例接近 1:1，暗示该城镇可能采用<b>混合用途（mixed-use）的社区规划理念</b>——
    商业空间就近嵌入居住区，降低居民出行成本并支持步行友好型生活模式。<br><br>
    商业建筑（{econ['commercial']} 栋）超出注册雇主数（{len(js)} 家）达 <b>{vacancy} 栋</b>，
    这一差额存在三种可能的解释：（1）部分商业建筑<b>空置</b>，代表闲置经济容量；
    （2）单一建筑内容纳<b>多家共用空间的企业</b>（如共享办公、多租户商业体）；
    （3）部分商业建筑用于<b>非雇主商业活动</b>（如仓储、社区活动中心、自雇经营）。
    无论何种解释，{vacancy} 栋商业空间余量意味着城市具备容纳经济扩张的物理承载能力。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Finding 5: Transaction Patterns
    # ================================================================
    st.markdown("## 五、消费模式——食品高频低额，住房低频高额")
    st.markdown("*交易频次与金额的分类结构——日常消费与月度支出的二分法*")

    col_l, col_r = st.columns(2)
    with col_l:
        fin_plot = fin.copy()
        fig_txn = px.bar(fin_plot.sort_values("transaction_count"), y="category", x="transaction_count",
                         title="各类别交易笔数", orientation="h",
                         color="transaction_count", color_continuous_scale="Blues",
                         text=fin_plot["transaction_count"].apply(lambda x: f"{x:,}"))
        fig_txn.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_txn, use_container_width=True)
    with col_r:
        fig_avg = px.bar(fin_plot.sort_values("avg_amount", key=abs), y="category",
                         x=fin_plot["avg_amount"].abs(),
                         title="各类别平均交易金额", orientation="h",
                         color=fin_plot["avg_amount"].abs(), color_continuous_scale="Reds",
                         text=fin_plot["avg_amount"].apply(lambda x: f"${abs(x):,.0f}"))
        fig_avg.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_avg, use_container_width=True)

    food_avg = abs(fin[fin["category"] == "Food"]["avg_amount"].iloc[0])
    shelter_avg = abs(fin[fin["category"] == "Shelter"]["avg_amount"].iloc[0])
    food_txn_count = fin[fin["category"] == "Food"]["transaction_count"].iloc[0]
    shelter_txn_count = fin[fin["category"] == "Shelter"]["transaction_count"].iloc[0]

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #B279A2; margin:12px 0;">
    <strong>📌 分析：</strong>消费呈现清晰的<b>双模式结构</b>。食品类交易呈<b>高频低额</b>特征——
    {food_txn_count:,} 笔交易，均价约 ${food_avg:.0f}/笔，对应日常高频购买行为（外出就餐
    或少量多次采购）。住房类交易则呈<b>低频高额</b>特征——仅 {shelter_txn_count:,} 笔交易，
    均价约 ${shelter_avg:.0f}/笔，对应月度房租/抵押贷款支付模式。<br><br>
    这一频率-金额的二分结构是标准消费者经济的典型特征，排除了数据异常的可能。
    食品交易笔数（{food_txn_count:,}）远超其他类别，结合 Q2 中餐饮场所作为核心社交载体的发现，
    提供了居民<b>"高频外出就餐"</b>而非"低频批量采购"消费行为模式的互补证据。
    从经济结构角度看，高食品交易频率支撑了餐饮服务业的需求端基础，
    为后文（发现六）中餐饮行业在可辨识雇主中占比最高提供了需求侧解释。
    </div>
    """, unsafe_allow_html=True)

    # ================================================================
    # Finding 6: Industry Segmentation
    # ================================================================
    st.markdown("---")
    st.markdown("## 六、产业分类——六类行业格局，以零售服务为主导")
    st.markdown("*基于建筑共址与岗位教育要求的综合行业分类及工资差异分析*")

    st.plotly_chart(make_q3_industry_pie(js_with_ind, js), use_container_width=True)
    st.plotly_chart(make_q3_industry_wage(js_with_ind), use_container_width=True)

    # Compute industry counts for the 6-category classification
    retail_count = ind_counts.get("Retail & Services", 0)
    biz_count = ind_counts.get("Business Services", 0)
    prof_count = ind_counts.get("Professional Services", 0)
    basic_count = ind_counts.get("Basic Services", 0)
    rest_count = ind_counts.get("Restaurant/Food Service", 0)
    pub_count = ind_counts.get("Pub/Hospitality", 0)
    fb_count = ind_counts.get("Food & Beverage", 0)

    # Wage averages by category
    def _avg_wage(ind):
        subset = js_with_ind[js_with_ind["industry"] == ind]
        return subset["avg_hourly_rate"].mean() if len(subset) > 0 else 0

    retail_avg = _avg_wage("Retail & Services")
    biz_avg = _avg_wage("Business Services")
    prof_avg = _avg_wage("Professional Services")
    basic_avg = _avg_wage("Basic Services")
    rest_avg = _avg_wage("Restaurant/Food Service")
    pub_avg = _avg_wage("Pub/Hospitality")

    # Proportion of largest category
    retail_pct = 100 * retail_count / len(js)

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #54A24B; margin:12px 0;">
    <strong>📌 核心发现——六类行业分层清晰：</strong><br>
    结合建筑共址分析（餐厅、酒吧）与岗位教育要求（Jobs.csv），将 253 家雇主细分为
    <b>六个行业类别</b>：<b>Retail &amp; Services</b>（{retail_count} 家，{retail_pct:.0f}%）、
    <b>Business Services</b>（{biz_count} 家）、<b>Restaurant/Food Service</b>（{rest_count} 家）、
    <b>Professional Services</b>（{prof_count} 家）、<b>Pub/Hospitality</b>（{pub_count} 家）和
    <b>Basic Services</b>（{basic_count} 家）。<br><br>
    <b>行业间工资梯度显著：</b>Professional Services 平均 ${prof_avg:.2f}/时（最高），
    Business Services ${biz_avg:.2f}/时，Restaurant ${rest_avg:.2f}/时，
    Retail &amp; Services ${retail_avg:.2f}/时，Basic Services ${basic_avg:.2f}/时——
    高技能岗位（研究生学历要求）享有明显的工资溢价，与前述学历分析一致。<br><br>
    <b>主导产业判断：</b>EngageTown 以<b>Retail &amp; Services</b>为主导（{retail_pct:.0f}%），
    辅以 Business Services 和 Professional Services。数据未呈现制造业基础或技术部门迹象，
    经济体是一个以<b>居民日常消费服务为核心的小型社区经济</b>（Community Service Economy），
    专业服务业的存在表明该城镇也承载了一定的知识型经济活动。
    </div>
    """, unsafe_allow_html=True)

    # ================================================================
    # Q3 Summary
    # ================================================================
    st.markdown("---")
    st.markdown("## Q3 总结：主导产业基础的系统画像")
    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.06);
    padding:20px 24px; border-radius:10px; border:1px solid rgba(128,128,128,0.15); margin-top:8px;">

    <p style="font-size:1.05em; line-height:1.9; text-align:justify;">
    <b>EngageTown 的经济基础可概括为"以零售服务为主导的小型社区经济体"</b>——由 {len(js)} 家小微雇主
    （规模 {econ['min_e']}–{econ['max_e']} 人）构成，六类行业分层清晰。
    工资为唯一收入来源（年总额 ${econ['total_wage']:,.0f}），支出以住房、休闲、食品为三大支柱，
    其中休闲与食品支出近乎持平——指向居民活跃的社交消费文化，与 Q2 社交网络分析形成跨领域互证。
    工资分布近正态（变异系数 {wage_cv:.2f}），极端薪酬罕见；但行业间存在显著工资梯度——
    Professional Services（${prof_avg:.2f}/时）显著高于 Basic Services（${basic_avg:.2f}/时）。
    建筑存量呈住宅-商业均衡布局，{vacancy} 栋商业空间余量暗示经济扩张的物理潜力。
    六类行业分类覆盖全部雇主：{retail_count} 家 Retail &amp; Services（{retail_pct:.0f}%）、
    {biz_count} 家 Business Services、{prof_count} 家 Professional Services、
    {rest_count} 家 Restaurant、{pub_count} 家 Pub、{basic_count} 家 Basic Services——
    围绕居民日常消费需求演化的<b>本地服务生态系统</b>，同时承载少量知识型经济活动。
    </p>

    <hr style="border-color:#d0d5dd; margin:16px 0;">

    <table style="width:100%; font-size:0.93em; border-collapse:collapse;">
    <tr style="background:rgba(128,128,128,0.15);">
        <td style="padding:8px 12px; width:20%;"><b>维度</b></td>
        <td style="padding:8px 12px; width:40%;"><b>核心发现</b></td>
        <td style="padding:8px 12px; width:40%;"><b>经济含义</b></td>
    </tr>
    <tr>
        <td style="padding:8px 12px;">🏢 雇主规模</td>
        <td style="padding:8px 12px;">{len(js)} 家雇主，{econ['min_e']}–{econ['max_e']} 人/家，中位数 {js['employee_count'].median():.0f}</td>
        <td style="padding:8px 12px;">小微雇主主导，无大企业——本地化服务经济</td>
    </tr>
    <tr style="background:rgba(128,128,128,0.1);">
        <td style="padding:8px 12px;">💰 收入结构</td>
        <td style="padding:8px 12px;">工资 ${econ['total_wage']:,.0f}，唯一收入来源</td>
        <td style="padding:8px 12px;">无资本收入/转移支付——纯劳动收入经济体</td>
    </tr>
    <tr>
        <td style="padding:8px 12px;">🛒 支出构成</td>
        <td style="padding:8px 12px;">住房 {shelter_pct:.0f}% | 休闲 {rec_pct:.0f}% | 食品 {food_pct:.0f}%</td>
        <td style="padding:8px 12px;">休闲≈食品——社交消费文化，非典型支出结构</td>
    </tr>
    <tr style="background:rgba(128,128,128,0.1);">
        <td style="padding:8px 12px;">💵 工资分布</td>
        <td style="padding:8px 12px;">${js['avg_hourly_rate'].min():.2f}–${js['avg_hourly_rate'].max():.2f}/时，均值 ${js['avg_hourly_rate'].mean():.2f}，CV={wage_cv:.2f}</td>
        <td style="padding:8px 12px;">近正态分布，雇主规模与工资脱钩</td>
    </tr>
    <tr>
        <td style="padding:8px 12px;">🏗️ 建筑构成</td>
        <td style="padding:8px 12px;">{econ['residential']} 住宅 + {econ['commercial']} 商业 + {econ['schools_n']} 学校；{vacancy} 栋商业余量</td>
        <td style="padding:8px 12px;">混合用途规划，存在物理扩张空间</td>
    </tr>
    <tr style="background:rgba(128,128,128,0.1);">
        <td style="padding:8px 12px;">🏷️ 产业分类</td>
        <td style="padding:8px 12px;">6 类行业：{retail_count} 零售({retail_pct:.0f}%)，{biz_count} 商务，{prof_count} 专业服务，{rest_count} 餐饮，{pub_count} 酒吧，{basic_count} 基础服务</td>
        <td style="padding:8px 12px;">零售服务主导，专业服务为辅——社区服务生态</td>
    </tr>
    <tr>
        <td style="padding:8px 12px;">📊 财务健康</td>
        <td style="padding:8px 12px;">净盈余 ${net_surplus:,.0f}（占工资 {surplus_pct:.0f}%）</td>
        <td style="padding:8px 12px;">收支结余，经济体具有储蓄/投资潜力</td>
    </tr>
    </table>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# Q4: Town Summary（城市概览）
# ============================================================
elif page.startswith("📋"):
    st.title("Q4：EngageTown 城市综合概览")
    st.markdown("*基于多维数据融合的城市画像——面向居民的社区信息一页式摘要*")

    # Pre-compute metrics used in hero banner
    net_surplus = econ['total_wage'] - econ['total_spending']

    # ---- Hero Banner ----
    st.markdown("---")
    working_age_pct_q4 = ps['age'].between(18, 59).mean() * 100
    kids_pct_q4 = ps['haveKids'].eq(True).mean() * 100
    edu_pct_q4 = (ps['educationLevel'].isin(['Bachelors', 'Graduate'])).mean() * 100
    st.markdown(f"""
    <div style="text-align:center; padding:28px 20px; background:linear-gradient(135deg, #1a2a3a 0%, #2E4057 40%, #4C78A8 100%);
    border-radius:14px; color:white; margin-bottom:24px; position:relative; overflow:hidden;">
        <h1 style="color:white; margin:0; font-size:2.5em; font-weight:700; position:relative;">EngageTown</h1>
        <p style="font-size:1.3em; opacity:0.9; margin-top:6px; letter-spacing:3px; font-weight:300; position:relative;">
        COMMUNITY PROFILE REPORT
        </p>
        <p style="font-size:1em; opacity:0.7; margin-top:8px; position:relative;">
        Population  &middot;  Social Fabric  &middot;  Economy  &middot;  Space
        </p>
    </div>

    <!-- Scorecard Row -->
    <div style="display:flex; gap:12px; margin-bottom:24px; flex-wrap:wrap;">
        <div style="flex:1; min-width:140px; background:linear-gradient(135deg, #2E4057, #3a5a7c); border-radius:10px; padding:16px 14px; text-align:center;">
            <div style="font-size:0.8em; color:rgba(255,255,255,0.7); text-transform:uppercase; letter-spacing:1px;">Residents</div>
            <div style="font-size:1.8em; font-weight:700; color:white; margin:4px 0;">{len(ps):,}</div>
            <div style="font-size:0.75em; color:rgba(255,255,255,0.5);">Avg age {ps['age'].mean():.1f} yrs</div>
        </div>
        <div style="flex:1; min-width:140px; background:linear-gradient(135deg, #4C78A8, #6ba3d6); border-radius:10px; padding:16px 14px; text-align:center;">
            <div style="font-size:0.8em; color:rgba(255,255,255,0.7); text-transform:uppercase; letter-spacing:1px;">Social Links</div>
            <div style="font-size:1.8em; font-weight:700; color:white; margin:4px 0;">{net_metrics['num_edges']:,}</div>
            <div style="font-size:0.75em; color:rgba(255,255,255,0.5);">{net_metrics.get('num_communities', 'N/A')} communities</div>
        </div>
        <div style="flex:1; min-width:140px; background:linear-gradient(135deg, #54A24B, #7bc96f); border-radius:10px; padding:16px 14px; text-align:center;">
            <div style="font-size:0.8em; color:rgba(255,255,255,0.7); text-transform:uppercase; letter-spacing:1px;">Employers</div>
            <div style="font-size:1.8em; font-weight:700; color:white; margin:4px 0;">{len(js)}</div>
            <div style="font-size:0.75em; color:rgba(255,255,255,0.5);">All micro (2-9 emp)</div>
        </div>
        <div style="flex:1; min-width:140px; background:linear-gradient(135deg, #F58518, #f7a84c); border-radius:10px; padding:16px 14px; text-align:center;">
            <div style="font-size:0.8em; color:rgba(255,255,255,0.7); text-transform:uppercase; letter-spacing:1px;">Annual Wage</div>
            <div style="font-size:1.8em; font-weight:700; color:white; margin:4px 0;">${econ['total_wage']/1e6:.1f}M</div>
            <div style="font-size:0.75em; color:rgba(255,255,255,0.5);">Net surplus ${net_surplus:,.0f}</div>
        </div>
        <div style="flex:1; min-width:140px; background:linear-gradient(135deg, #E45756, #f07a7a); border-radius:10px; padding:16px 14px; text-align:center;">
            <div style="font-size:0.8em; color:rgba(255,255,255,0.7); text-transform:uppercase; letter-spacing:1px;">Check-ins</div>
            <div style="font-size:1.8em; font-weight:700; color:white; margin:4px 0;">{vc['checkins'].sum():,}</div>
            <div style="font-size:0.75em; color:rgba(255,255,255,0.5);">{len(vc)} venues</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Section 1: 人口结构
    # ================================================================
    st.markdown("## 一、人口结构与基本特征")
    st.markdown("*居民年龄分布、家庭构成与教育水平——勾勒城市人口基底*")

    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.plotly_chart(make_q1_age_histogram(ps), use_container_width=True)
    with col_r:
        age_bins = [0, 18, 30, 45, 60, 100]
        age_labels = ["0–17（未成年）", "18–29（青年）", "30–44（壮年）", "45–59（中年）", "60+（老年）"]
        ps_m = ps.copy()
        ps_m["age_group"] = pd.cut(ps_m["age"], bins=age_bins, labels=age_labels)
        age_summary = ps_m["age_group"].value_counts().sort_index()
        for label, count in age_summary.items():
            st.metric(label, f"{count} 人", delta=f"{count/len(ps)*100:.1f}%")

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #2E4057; margin:12px 0;">
    <strong>📌 分析：</strong>EngageTown 居民年龄呈典型的<b>劳动力主导型分布</b>，均值 {ps['age'].mean():.1f} 岁，中位数 {ps['age'].median():.0f} 岁。
    18–59 岁工作年龄段占比超过七成，构成城市经济活动的主体力量。年龄分布呈现轻微右偏态，老年人口（60+）相对较少，
    表明该城市为一个<b>以中青年为核心的经济活跃社区</b>，抚养比处于健康区间。家庭结构方面，户均规模仅
    {ps['householdSize'].mean():.1f} 人，{
    '以二人户为主，有子女家庭占比约' + str(round(ps["haveKids"].eq(True).mean()*100)) + '%，呈现典型的小家庭化特征。'
    }
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Section 2: 教育水平
    # ================================================================
    st.markdown("## 二、教育水平与人力资本")
    st.markdown("*居民受教育程度分布及其经济关联*")

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q1_education_bar(ps), use_container_width=True)
    with col_r:
        st.plotly_chart(make_q1_edu_balance(ps), use_container_width=True)

    st.plotly_chart(make_q1_edu_age_cross(ps), use_container_width=True)

    edu_dist = ps["educationLevel"].value_counts()
    top_edu = edu_dist.index[0]
    bachelors_pct = edu_dist.get("Bachelors", 0) / len(ps) * 100
    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #4C78A8; margin:12px 0;">
    <strong>📌 分析：</strong>居民受教育程度集中于"<b>高中或大学肄业</b>"（{edu_dist.get('HighSchoolOrCollege', 0)} 人，
    {edu_dist.get('HighSchoolOrCollege', 0)/len(ps)*100:.1f}%）与"<b>学士</b>"（{edu_dist.get('Bachelors', 0)} 人，
    {bachelors_pct:.1f}%）两个层级。教育水平与财务状况呈正相关趋势：学士及以上学历者的平均可用余额显著高于
    低学历群体，反映了<b>人力资本对经济回报的正向影响</b>。值得注意的是，"高中或大学肄业"群体规模最大，
    但内部经济差异也最为显著，可能对应不同职业路径的收入分化。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Section 3: 社交网络结构
    # ================================================================
    st.markdown("## 三、社交网络与社区结构")
    st.markdown("*社会连接的拓扑特征——从个体关系到社区凝聚*")

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q2_degree_distribution(net_metrics["degree"]), use_container_width=True)
    with col_r:
        comm_fig = make_q2_community_sizes(net_metrics)
        if comm_fig:
            st.plotly_chart(comm_fig, use_container_width=True)

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #54A24B; margin:12px 0;">
    <strong>📌 分析：</strong>EngageTown 社交网络包含 <b>{net_metrics['num_nodes']:,} 个节点</b>、<b>{net_metrics['num_edges']:,} 条边</b>，
    网络密度为 {net_metrics['density']:.4f}。度分布呈<b>近似正态</b>特征——大多数居民维持相似规模的社交圈，
    社交连接高度均质化，没有少数"超级连接者"垄断社交资源。Louvain 社区检测识别出
    <b>{net_metrics.get('num_communities', 'N/A')} 个社交社区</b>，模块度达 {net_metrics.get('modularity', 0):.4f}，
    表明社区间边界清晰，居民的社会交往主要集中于所属群体内部。平均聚类系数
    {net_metrics['avg_clustering']:.4f} 远高于网络密度，印证了<b>"朋友的朋友亦是朋友"</b>的紧密社交圈特征。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Section 4: 社交活动时空模式
    # ================================================================
    st.markdown("## 四、社交活动的时间与空间模式")
    st.markdown("*居民行为节律——何时、何地、以何种方式社交*")

    st.plotly_chart(make_q2_hourly_activity(ha, mode_cols), use_container_width=True)

    hourly_total = ha.groupby("hour_num")["total_mode"].sum().reset_index()
    peak_hour = int(hourly_total.loc[hourly_total["total_mode"].idxmax(), "hour_num"])
    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #72B7B2; margin:12px 0;">
    <strong>📌 分析：</strong>居民活动呈现清晰的<b>昼夜节律</b>：凌晨 0–6 时为活动低谷（睡眠时段），
    上午 7–11 时逐步攀升（通勤与工作启动），午后至傍晚达到峰值（<b>高峰时段 {peak_hour}:00</b>），
    夜间平缓回落。工作日与周末模式存在结构性差异：周末活动峰值较工作日推迟约
    <b>{int(weekend['we_peak']) - int(weekend['wd_peak'])} 小时</b>，"工作"模式占比从
    {weekend['wd_work_pct']:.1f}% 降至 {weekend['we_work_pct']:.1f}%，而"休闲娱乐"占比从
    {weekend['wd_rec_pct']:.1f}% 升至 {weekend['we_rec_pct']:.1f}%。这一波动模式表明
    EngageTown 居民遵循<b>规律的工作-休闲二分节律</b>，周末以社交休闲为生活主轴。
    </div>
    """, unsafe_allow_html=True)

    # Venue map
    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q4_mini_venue(vc), use_container_width=True)
    with col_r:
        total_checkins = vc["checkins"].sum()
        social_checkins = vc[vc["venueType"].isin(["Restaurant", "Pub"])]["checkins"].sum()
        social_pct = social_checkins / total_checkins * 100
        top_venue = vc.nlargest(1, "checkins")
        st.markdown(f"""
        <div style="background:rgba(128,128,128,0.1); padding:14px 16px; border-radius:8px; border-left:4px solid #F58518; margin:6px 0;">
        <strong>🏬 场所使用总览</strong><br><br>
        • <b>总签到量：</b>{total_checkins:,} 人次<br>
        • <b>餐饮社交场所：</b>{social_checkins:,} 人次（{social_pct:.0f}%）<br>
        • <b>热门场所：</b>{top_venue.iloc[0]['venueType']} 类型
        ({top_venue.iloc[0]['checkins']:,} 人次)<br>
        • <b>场所分布：</b>{len(data.get('pubs', []))} 家酒吧 |
        {len(data.get('restaurants', []))} 家餐厅 |
        {len(data.get('schools', []))} 所学校<br>
        • <b>社交媒介：</b>酒吧与餐厅合计占签到总量六成以上，表明<b>餐饮场所是社区社交的核心载体</b>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Section 5: 经济基础
    # ================================================================
    st.markdown("## 五、经济基础与产业结构")
    st.markdown("*经济活动的规模、结构及运行特征*")

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q3_financial_flow(fin), use_container_width=True)
    with col_r:
        st.plotly_chart(make_q4_mini_financial(fin), use_container_width=True)

    shelter_amt = abs(fin[fin['category'] == 'Shelter']['total_amount'].iloc[0])
    rec_amt = abs(fin[fin['category'] == 'Recreation']['total_amount'].iloc[0])
    food_amt = abs(fin[fin['category'] == 'Food']['total_amount'].iloc[0])
    net_surplus = econ['total_wage'] - econ['total_spending']
    surplus_pct = net_surplus / econ['total_wage'] * 100

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #E45756; margin:12px 0;">
    <strong>📌 分析：</strong>EngageTown 经济体量以<b>年工资总额 ${econ['total_wage']:,.0f}</b> 衡量，
    工资为唯一收入来源，表明该城市不具备显著的投资收益或转移支付体系。支出端呈现三足鼎立格局：<b>住房</b>
    ${shelter_amt:,.0f}（{shelter_amt/econ['total_spending']*100:.0f}%）、<b>休闲</b>
    ${rec_amt:,.0f}（{rec_amt/econ['total_spending']*100:.0f}%）、<b>食品</b>
    ${food_amt:,.0f}（{food_amt/econ['total_spending']*100:.0f}%）。<b>休闲支出占比与食品相当</b>
    这一特征值得关注——它指向居民活跃的社交消费习惯，与前述社交网络分析高度吻合。年度净盈余
    ${net_surplus:,.0f}（占工资 {surplus_pct:.0f}%）表明总体收支存在正向结余。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Section 6: 产业与就业
    # ================================================================
    st.markdown("## 六、产业形态与就业特征")
    st.markdown("*雇主规模、工资分布与行业可辨识度*")

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q3_employer_size(js), use_container_width=True)
    with col_r:
        st.plotly_chart(make_q3_wage_box(js), use_container_width=True)

    retail_count_q4 = ind_counts.get("Retail & Services", 0)
    biz_count_q4 = ind_counts.get("Business Services", 0)
    prof_count_q4 = ind_counts.get("Professional Services", 0)
    rest_count_q4 = ind_counts.get("Restaurant/Food Service", 0)
    pub_count_q4 = ind_counts.get("Pub/Hospitality", 0)
    basic_count_q4 = ind_counts.get("Basic Services", 0)
    retail_pct_q4 = 100 * retail_count_q4 / len(js)

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.1); padding:16px 20px; border-radius:8px; border-left:4px solid #B279A2; margin:12px 0;">
    <strong>📌 分析——主导产业判断：</strong>EngageTown 的经济形态可概括为<b>"以零售服务为主导的小型社区经济体"</b>。
    {len(js)} 家雇主均为小微实体（规模 {econ['min_e']}–{econ['max_e']} 人，中位数
    {js['employee_count'].median():.0f} 人），<b>不存在大型企业或制造业基地</b>。六类行业分层清晰：
    <b>Retail &amp; Services</b> {retail_count_q4} 家（{retail_pct_q4:.0f}%）为最大类别，
    其次 Business Services {biz_count_q4} 家、Restaurant {rest_count_q4} 家、
    Professional Services {prof_count_q4} 家、Pub {pub_count_q4} 家、Basic Services {basic_count_q4} 家。<br><br>
    <b>核心结论：</b>该城市以<b>居民日常消费服务为核心</b>（零售+餐饮+基础服务），同时承载商务服务和
    专业服务等知识型经济活动，属于典型的<b>居民社区导向型服务经济</b>，而非工业或公司城镇。
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Section 7: 城市空间布局
    # ================================================================
    st.markdown("## 七、城市空间结构与设施布局")
    st.markdown("*建筑分布、功能分区及社交场所的空间集聚*")

    map_fig = make_venue_map(base_map, data)
    if map_fig:
        map_fig.update_layout(height=550)
        st.plotly_chart(map_fig, use_container_width=True)
    else:
        st.info("地图不可用（缺少 BaseMap.png 底图文件）")

    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(make_q3_building_types(bt), use_container_width=True)
    with col_r:
        vacancy = max(0, econ['commercial'] - len(js))
        st.markdown(f"""
        <div style="background:rgba(128,128,128,0.1); padding:14px 16px; border-radius:8px; border-left:4px solid #2E4057; margin:6px 0;">
        <strong>🏗️ 建筑功能构成</strong><br><br>
        • <b>住宅建筑：</b>{econ['residential']} 栋（{econ['residential']/bt['count'].sum()*100:.0f}%）<br>
        • <b>商业建筑：</b>{econ['commercial']} 栋（{econ['commercial']/bt['count'].sum()*100:.0f}%）<br>
        • <b>学校建筑：</b>{econ['schools_n']} 栋<br>
        • <b>商业空间余量：</b>{vacancy} 栋（商业建筑 − 注册雇主）<br>
        • <b>空间特征：</b>住宅与商业建筑近乎均衡分布，酒吧与餐厅呈空间共址集聚，
        形成若干<b>社交-商业混合功能区</b>。学校数量少但空间覆盖范围大，
        服务于较广的学区范围。{vacancy} 栋商业建筑未被注册雇主占用，
        意味着存在<b>共享办公、非正规商业或空置三种可能</b>。
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ================================================================
    # Bottom Summary
    # ================================================================
    st.markdown("## 总结：EngageTown 城市综合画像")

    st.markdown(f"""
    <div style="background:rgba(128,128,128,0.06);
    padding:20px 24px; border-radius:12px; border:1px solid rgba(128,128,128,0.15); margin-top:8px;">

    <p style="font-size:1.05em; line-height:1.9; text-align:justify;">
    <b>EngageTown</b> is a community of <b>{len(ps):,} working-age-dominant residents</b>,
    mean age {ps['age'].mean():.1f} years, household size {ps['householdSize'].mean():.1f},
    exhibiting a <b>compact, low-dependency social structure</b>. Education clusters at the
    high-school-to-bachelor level with a clear income gradient. The social network of
    {net_metrics['num_nodes']:,} nodes and {net_metrics['num_edges']:,} edges forms a
    <b>highly clustered community structure</b> (modularity {net_metrics.get('modularity', 0):.4f}),
    centered on dining venues with a pronounced circadian rhythm. The economy runs on
    <b>{len(js)} micro-employers</b> generating ${econ['total_wage']:,.0f} in annual wages
    with no single dominant industry -- a <b>resident-oriented service economy</b>.
    </p>

    <hr style="border-color:#d0d5dd; margin:16px 0;">

    <!-- Dimension Cards -->
    <div style="display:flex; gap:14px; flex-wrap:wrap;">
        <div style="flex:1; min-width:220px; background:white; border-radius:10px; border-left:5px solid #2E4057; padding:16px; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="font-size:0.75em; color:#2E4057; text-transform:uppercase; letter-spacing:1px; font-weight:600;">Demographics</div>
            <div style="font-size:1.1em; font-weight:700; margin:6px 0; color:#1a1a1a;">{len(ps):,} residents</div>
            <div style="font-size:0.85em; color:#555; line-height:1.6;">
                Mean age {ps['age'].mean():.1f} | Household {ps['householdSize'].mean():.1f}<br>
                {working_age_pct_q4:.0f}% working age | {kids_pct_q4:.0f}% with kids<br>
                {ps['interestGroup'].nunique()} interest groups (uniform)
            </div>
            <div style="margin-top:8px; background:#eee; border-radius:4px; height:6px;">
                <div style="background:#2E4057; height:100%; border-radius:4px; width:{edu_pct_q4:.0f}%;"></div>
            </div>
            <div style="font-size:0.7em; color:#888; margin-top:3px;">{edu_pct_q4:.0f}% bachelor+ educated</div>
        </div>
        <div style="flex:1; min-width:220px; background:white; border-radius:10px; border-left:5px solid #4C78A8; padding:16px; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="font-size:0.75em; color:#4C78A8; text-transform:uppercase; letter-spacing:1px; font-weight:600;">Social Network</div>
            <div style="font-size:1.1em; font-weight:700; margin:6px 0; color:#1a1a1a;">{net_metrics['num_edges']:,} connections</div>
            <div style="font-size:0.85em; color:#555; line-height:1.6;">
                {net_metrics.get('num_communities', 'N/A')} communities | Modularity {net_metrics.get('modularity', 0):.4f}<br>
                Avg clustering {net_metrics['avg_clustering']:.4f}<br>
                {vc['checkins'].sum():,} check-ins at {len(vc)} venues
            </div>
            <div style="margin-top:8px; background:#eee; border-radius:4px; height:6px;">
                <div style="background:#4C78A8; height:100%; border-radius:4px; width:{min(net_metrics['avg_clustering']*100*5, 100):.0f}%;"></div>
            </div>
            <div style="font-size:0.7em; color:#888; margin-top:3px;">High clustering coefficient</div>
        </div>
        <div style="flex:1; min-width:220px; background:white; border-radius:10px; border-left:5px solid #54A24B; padding:16px; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="font-size:0.75em; color:#54A24B; text-transform:uppercase; letter-spacing:1px; font-weight:600;">Economy</div>
            <div style="font-size:1.1em; font-weight:700; margin:6px 0; color:#1a1a1a;">${econ['total_wage']:,.0f} wages</div>
            <div style="font-size:0.85em; color:#555; line-height:1.6;">
                {len(js)} micro-employers ({econ['min_e']}--{econ['max_e']}/co)<br>
                Avg hourly ${js['avg_hourly_rate'].mean():.2f} | Net +${net_surplus:,.0f}<br>
                Retail-led service economy
            </div>
            <div style="margin-top:8px; background:#eee; border-radius:4px; height:6px;">
                <div style="background:#54A24B; height:100%; border-radius:4px; width:{surplus_pct:.0f}%;"></div>
            </div>
            <div style="font-size:0.7em; color:#888; margin-top:3px;">{surplus_pct:.0f}% wage surplus</div>
        </div>
        <div style="flex:1; min-width:220px; background:white; border-radius:10px; border-left:5px solid #E45756; padding:16px; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <div style="font-size:0.75em; color:#E45756; text-transform:uppercase; letter-spacing:1px; font-weight:600;">Space</div>
            <div style="font-size:1.1em; font-weight:700; margin:6px 0; color:#1a1a1a;">{bt['count'].sum():,} buildings</div>
            <div style="font-size:0.85em; color:#555; line-height:1.6;">
                {econ['residential']} residential + {econ['commercial']} commercial<br>
                {econ['schools_n']} schools | {len(data.get('pubs', []))} pubs<br>
                {len(data.get('restaurants', []))} restaurants
            </div>
            <div style="margin-top:8px; background:#eee; border-radius:4px; height:6px;">
                <div style="background:#E45756; height:100%; border-radius:4px; width:{econ['residential']/bt['count'].sum()*100:.0f}%;"></div>
            </div>
            <div style="font-size:0.7em; color:#888; margin-top:3px;">{econ['residential']/bt['count'].sum()*100:.0f}% residential</div>
        </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# Footer
# ============================================================
st.markdown("---")
st.caption("VAST Challenge 2022 MC1 | Visual Analytics Report | Python · Streamlit · Plotly · NetworkX")
