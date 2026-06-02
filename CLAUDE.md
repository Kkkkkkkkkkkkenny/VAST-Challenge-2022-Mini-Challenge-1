# VAST Challenge 2022 MC1 — EngageTown Dashboard

## 项目目标
完成 Mini-Challenge 1：EngageTown 虚构城市的可视化分析。
用数据回答 4 个问题，最终产出分析报告（analysis report）而非数据浏览器。

## 当前状态：V2 分析报告（2026-06-02）

app.py 已从 V1 数据浏览器升级为分析报告风格 Dashboard：
- Q1: 5 个分析发现 + 交叉分析 + 结论
- Q2: 10 个社交模式，每个 = 图表 + 量化证据
- Q3: 识别主导产业（小型服务经济）+ 5 个经济发现
- Q4: 三栏信息图风格一页摘要 + 地图

### 关键架构决策
- **社交网络分析在 app.py 内完成**（`compute_network_metrics()`），使用 `@st.cache_data` 缓存，未修改 process_data.py。
  - 如果社交网络指标需要被多地复用或数据量增大，考虑将其移入 process_data.py 预计算。
- **所有图表数据均为动态计算**，不包含硬编码数值，确保数据更新后自动反映。
- **HTML 内容使用 `unsafe_allow_html=True`**，用于分析框（蓝色/绿色/红色左边框卡片）。

## 关键文件
| 文件 | 用途 |
|---|---|
| `app.py` | Streamlit Dashboard，4 页分析报告，动态读取 processed/ 下的 parquet |
| `process_data.py` | 数据管道：114M 活动日志 + 13.5M 日志 → 14 个 parquet。一次运行，生成 processed/ |
| `Datasets/` | 原始 CSV（gitignored，~3GB） |
| `processed/` | 输出的 parquet（gitignored，14 个文件，~1.3MB） |
| `BaseMap.png` | 城市底图，用于 Q2/Q4 地图标注 |
| `docs/superpowers/specs/2026-05-30-mc1-improvement-plan.md` | 改进计划（部分已完成，见下方） |

## processed/ 数据文件一览
| 文件 | 行数 | 来源 | 用途 |
|---|---|---|---|
| `participant_summary.parquet` | 1,011 | Attributes + Activity + Social | Q1-Q4 核心人口数据 |
| `social_network.parquet` | 160,966 | SocialNetwork journal | Q2 网络分析 |
| `venue_checkins.parquet` | 1,114 | CheckinJournal | Q2 签到分析 |
| `hourly_activity.parquet` | 10,774 | Activity logs | Q2 时间模式 |
| `daily_activity.parquet` | 450 | Activity logs | 每日活动趋势 |
| `financial_summary.parquet` | 6 | FinancialJournal | Q3 财务分析 |
| `daily_financial.parquet` | 1,391 | FinancialJournal | 每日财务趋势 |
| `job_summary.parquet` | 253 | Jobs.csv | Q3 雇主/工资分析 |
| `travel_purpose_summary.parquet` | 5 | TravelJournal | Q2 出行模式 |
| `building_types.parquet` | 3 | Buildings.csv | Q3 建筑类型 |
| `pubs.parquet` | 12 | Pubs.csv | Q2/Q4 地图标注 |
| `restaurants.parquet` | 20 | Restaurants.csv | Q2/Q4 地图标注 |
| `schools.parquet` | 4 | Schools.csv | Q2/Q4 地图标注 |
| `apartments.parquet` | 1,517 | Apartments.csv | 公寓数据 |

## 数据来源映射
```
原始 CSV                          → 处理脚本                       → 输出 parquet
============================================================================================
Activity Logs (72 files, 114M行)   → process_activity_logs()        → participant_summary (partial)
                                                                     hourly_activity
                                                                     daily_activity
Attributes/*.csv                   → load_attributes()               → (merged into participant_summary)
                                                                     pubs, restaurants, schools, apartments
CheckinJournal.csv                 → process_checkin_journal()      → venue_checkins
FinancialJournal.csv               → process_financial_journal()    → financial_summary, daily_financial
SocialNetwork.csv                  → process_social_network()       → social_network
TravelJournal.csv                  → process_travel_journal()       → travel_purpose_summary
Jobs.csv + Employers.csv           → build_job_summaries()          → job_summary, building_types
```

## app.py 架构
```
数据加载 (st.cache_data)
├── load_data()          → 读所有 processed/*.parquet
├── load_base_map()      → BaseMap.png → base64
├── compute_network_metrics() → networkx 图分析 (社区检测/中心性/聚类)
└── compute_cross_analysis()  → 人口 × 社交交叉分析

页面渲染
├── Q1 Demographics      → 5 个 Finding + Hero metrics + Summary
├── Q2 Social Activities → 10 个 Pattern + Network overview + Summary
├── Q3 Business          → 5 个 Finding + 经济指标 + Summary
└── Q4 Town Summary      → 三栏信息图 + 地图 + 底部摘要
```

## 技术栈
- Python 3.14, pandas, fastparquet, plotly 6.7, streamlit 1.58
- networkx 3.6（社区检测、中心性指标）
- 运行：`streamlit run app.py`
- 数据处理：`python3 process_data.py`（耗时约 5-10 分钟）
- Tailscale IP：100.81.74.3

## 待完成工作

### 高优先
- [ ] **Answer Sheet 生成**：MC1 最终提交格式是 Answer Sheet HTML。需要从分析结果中导出静态图表和 500 字答案文本。
- [ ] **Q2 Pattern 证据加强**：部分模式的量化证据仍偏弱（如 Pattern 5 的峰值 "17:00"、Pattern 6 的趋势线显著性），需要补充更多统计检验。
- [ ] **Q3 产业分类**：当前用"小型企业"概括，如果能结合 employer 名称/位置进一步推断行业类型会更精确。

### 中优先
- [ ] Q1 增加教育-年龄交叉分析图
- [ ] Q2 增加工作日 vs 周末行为对比（需要从 hourly/daily activity 中提取星期信息）
- [ ] Q4 信息图更加视觉化（如使用自定义 HTML/CSS 布局替代 streamlit 原生组件）
- [ ] 考虑用户体验：当前 st.cache_data 在首次加载网络指标时会有 10-30 秒延迟

### 低优先（Phase 6 打磨）
- [ ] 配色方案统一（当前使用混合调色板）
- [ ] 图表增加注释和来源说明
- [ ] 左侧导航优化（可能改为"报告模式"单页滚动）
- [ ] 移动端响应式布局

### 已知问题
- buildingTypes 数据有拼写错误："Residental" 应为 "Residential"（源自原始 CSV）
- 部分 venue 的 "maxOccupancy " 列名有尾随空格（process_data.py 已做 rename 处理）
- Playwright 不支持 ubuntu 26.04，无法用 webapp-testing skill 截图

## Git
- 分支：master（上游 main）
- Datasets/、processed/、venv/ 已 gitignore
- 提交风格：英文，简洁描述
