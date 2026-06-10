# VAST Challenge 2022 — Mini-Challenge 1: EngageTown

EngageTown 虚构城市的可视化分析项目。参与 [IEEE VAST Challenge 2022](https://vast-challenge.github.io/2022/) Mini-Challenge 1，用数据回答 4 个问题，产出分析报告式 Dashboard 和答题卷（Answer Sheet HTML）。

---

## 目录

- [项目概览](#项目概览)
- [快速上手](#快速上手)
- [项目结构](#项目结构)
- [GitHub 上传准备](#github-上传准备)
- [技术栈与依赖](#技术栈与依赖)
- [数据流与工作流程](#数据流与工作流程)
- [关键架构决策](#关键架构决策)
- [本阶段变更记录（2026-06-02 → 2026-06-10）](#本阶段变更记录)
- [当前产出状态](#当前产出状态)
- [待完成工作](#待完成工作)
- [已知问题](#已知问题)
- [给接手指南](#给接手指南)
- [参考文献](#参考文献)

---

## 项目概览

| 维度 | 现状 |
|------|------|
| **目标** | 完成 MC1 四问分析，产出 Answer Sheet HTML 提交 |
| **数据规模** | 1.14 亿条活动日志 + 13.5M 条日志 / 1,011 名志愿者 / 15 个月 |
| **核心产出** | `app.py`（分析 Dashboard）+ `Answer Sheets/index.htm`（最终提交） |
| **支持文件** | `common.py`（共享分析引擎）+ `process_data.py`（数据管道）+ `export_answer_sheet.py`（静态导出） |
| **总代码量** | ~4,600 行 Python + ~550 行 HTML |
| **当前版本** | V2.1（2026-06-10） |

**四个问题：**

| Q | 主题 | 图表 | 词限 | 已产出 |
|---|------|------|------|--------|
| Q1 | 人口特征 | 9 幅 | 500 词 | 5 项发现 + 交叉分析 |
| Q2 | 社交活动 | 11 幅 | 500 词 | 10 项社交模式（三板块） |
| Q3 | 商业经济 | 9 幅 | 500 词 | 5 项经济发现 + 产业判定 |
| Q4 | 城市概览 | 4 幅 | 一页 | 信息图 + 场所地图 |

---

## 快速上手

### 环境要求

- **Python** 3.11+
- **操作系统**：Windows / macOS / Linux
- **磁盘空间**：~4GB（原始 CSV ~3GB + 处理后 ~50MB）

### 安装依赖

```bash
pip install pandas fastparquet plotly streamlit networkx kaleido
```

| 包 | 用途 |
|----|------|
| `pandas` + `fastparquet` | 数据处理与 parquet 读写 |
| `plotly` + `kaleido` | 交互式图表 + 静态 PNG 导出 |
| `streamlit` | 分析报告 Web Dashboard |
| `networkx` | 社交网络分析（社区检测、中心性） |

### 启动项目

```bash
# 步骤 1：处理原始数据（首次运行，约 5-10 分钟）
python3 process_data.py

# 步骤 2：启动分析 Dashboard
streamlit run app.py
# 浏览器访问 → http://localhost:8501

# 步骤 3（可选）：生成静态 Answer Sheet
python3 export_answer_sheet.py
# 输出 → Answer Sheets/index.htm + 33 张 PNG 图表
```

> **注意**：步骤 1 需要将 VAST Challenge 2022 官方数据包中的 `Datasets/` 目录放置到项目同级目录的 `VAST-Challenge-2022/VAST-Challenge-2022/Datasets/` 路径下。

### 路径约定

```
../VAST-Challenge-2022/VAST-Challenge-2022/
├── Datasets/          # 原始 CSV（官方数据包，~3GB，gitignored）
│   ├── Activity Logs/ # 72 个 CSV 文件
│   ├── Journals/      # CheckinJournal, FinancialJournal, SocialNetwork, TravelJournal
│   └── Attributes/    # Participants, Employers, Jobs, Buildings, Pubs, Restaurants, Schools, Apartments
└── BaseMap.png        # 城市底图

本项目根目录/
├── processed/         # 输出的 parquet 文件（14 个，~1.3MB，gitignored）
└── Answer Sheets/     # 答题卷 + 33 张图表 PNG
```

---

## 项目结构

### 核心文件

```
.
├── app.py                          # Streamlit Dashboard — 4 页分析报告（中文，1,466 行）
├── common.py                       # 共享分析引擎 — 数据加载/图表生成/网络分析（1,218 行）
├── process_data.py                 # 数据管道 — 114M 活动日志 → 14 个 parquet（494 行）
├── export_answer_sheet.py          # 静态导出 — 生成 Answer Sheet HTML + 33 张 PNG（910 行）
│
├── CLAUDE.md                       # 🔧 开发者指南（数据源映射、架构、待办、已知问题）
├── README.md                       # 📖 本文件 — 项目总览、变更记录、接手指南
│
├── Answer Sheets/
│   ├── index.htm                   # 答题卷 HTML（中文，548 行，含分析推理）
│   └── VAST Challenge 2022 C1 Answer Sheet_files/
│       ├── chart_q1_01.png ...     # Q1 9 张图表
│       ├── chart_q2_01.png ...     # Q2 11 张图表
│       ├── chart_q3_01.png ...     # Q3 9 张图表
│       └── chart_q4_01.png ...     # Q4 4 张图表（含地图）
│
├── docs/
│   └── superpowers/
│       ├── specs/2026-05-30-mc1-improvement-plan.md  # 改进计划（部分已完成）
│       └── plans/2026-05-30-mc1-pipeline-fix.md      # 历史：管道修复计划
│
└── .gitignore                      # 排除原始数据、中间产物；保留源代码和答题卷
```

### 文件职责分工

| 文件 | 角色 | 被谁依赖 | 可独立运行 |
|------|------|----------|-----------|
| `common.py` | **唯一数据源（Single Source of Truth）** — 所有数据加载、图表生成、网络分析 | `app.py`、`export_answer_sheet.py` | 否（被导入） |
| `app.py` | **分析报告 UI** — Streamlit 4 页 Dashboard，读 `common.py` 的函数渲染页面 | 无 | `streamlit run app.py` |
| `export_answer_sheet.py` | **静态导出器** — 用 kaleido 导出 Plotly 图表为 PNG，生成 `index.htm` | 无 | `python3 export_answer_sheet.py` |
| `process_data.py` | **数据管道** — 从原始 CSV 生成 `processed/*.parquet` | 前三个文件（通过 `processed/` 间接依赖） | `python3 process_data.py` |
| `index.htm` | **最终提交物** — VAST Challenge Answer Sheet | 无（纯静态 HTML） | 浏览器直接打开 |

### processed/ 数据文件一览

| 文件 | 行数 | 来源 | 用途 |
|------|------|------|------|
| `participant_summary.parquet` | 1,011 | Attributes + Activity + Social | Q1–Q4 核心人口数据 |
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

---

## GitHub 上传准备

### 追踪策略

本项目遵循 GitHub 最佳实践：**追踪源代码和最终成果，忽略原始数据和中间产物**。

### 上传时包含的文件（`git add`）

| 类别 | 文件 | 说明 |
|------|------|------|
| **核心脚本** | `app.py`, `common.py`, `process_data.py`, `export_answer_sheet.py` | 全部 Python 源代码（~4,600 行） |
| **配置文件** | `.gitignore` | 忽略规则 |
| **文档** | `README.md`, `CLAUDE.md` | 项目说明 + 开发者指南 |
| **历史规划** | `docs/superpowers/specs/*.md`, `docs/superpowers/plans/*.md` | 改进计划与管道修复记录 |
| **答题卷** | `Answer Sheets/index.htm` | VAST Challenge 最终提交 HTML（548 行） |
| **答题卷图表** | `Answer Sheets/VAST Challenge 2022 C1 Answer Sheet_files/*.png` | 33 张 PNG 图表（~2MB） |
| **答题卷动画** | `Answer Sheets/.../chart_q2_12_hourly_animation.gif` | Q2 小时活动动画（~2MB） |

### 被忽略的文件（`.gitignore` 排除）

| 类别 | 路径/模式 | 原因 | 如何获取 |
|------|-----------|------|----------|
| **原始数据** | `Datasets/` | ~3GB CSV，官方数据包，版权不属于本项目 | 从 [VAST Challenge 2022](https://vast-challenge.github.io/2022/) 下载 |
| **中间产物** | `processed/`, `*.parquet` | 由 `process_data.py` 生成，约 1.3MB | 运行 `python3 process_data.py` |
| **虚拟环境** | `venv/`, `.venv/`, `env/` | 本地环境，各机器不同 | `pip install pandas fastparquet plotly streamlit networkx kaleido` |
| **IDE 配置** | `.idea/`, `.vscode/`, `*.swp` | 个人编辑器设置 |
| **Python 缓存** | `__pycache__/`, `*.pyc` | 字节码缓存，可重新生成 |
| **Claude 会话** | `.claude/` | AI 辅助开发会话，与代码无关 |
| **Streamlit 密钥** | `.streamlit/secrets.toml` | 可能包含敏感信息 |
| **系统文件** | `.DS_Store`, `Thumbs.db`, `Desktop.ini` | 操作系统自动生成 |

### 上传后的操作（克隆者视角）

```bash
# 1. 克隆仓库
git clone <repo-url>
cd VAST-Challenge-2022-Mini-Challenge-1-master

# 2. 安装依赖
pip install pandas fastparquet plotly streamlit networkx kaleido

# 3. 下载原始数据 → 放置到 ../VAST-Challenge-2022/VAST-Challenge-2022/Datasets/
#    从 https://vast-challenge.github.io/2022/ 获取

# 4. 运行数据管道
python3 process_data.py    # 生成 processed/*.parquet

# 5. 启动分析 Dashboard
streamlit run app.py       # → http://localhost:8501

# 6. （可选）重新生成 Answer Sheet 图表
python3 export_answer_sheet.py
```

### 发行包说明

项目根目录提供 `RELEASE_INFO.md`，详细记录了本次 GitHub 上传准备的完整变更清单，包括：
- `.gitignore` 修改前后对比
- 每类文件的追踪/忽略决策依据
- 上传包文件清单（SHA256 校验）
- 数据再生指南

### .gitignore 规则速查

```
追踪（上传）          忽略（不上传）
──────────────       ──────────────────
app.py               Datasets/（~3GB 原始 CSV）
common.py            processed/（~1.3MB parquet）
process_data.py      __pycache__/
export_answer_sheet.py  venv/
README.md            .claude/
CLAUDE.md            .idea/ .vscode/
.gitignore           .DS_Store Thumbs.db
docs/                *.log *.tmp
Answer Sheets/       *.pyc
  (HTML + PNG/GIF)
```

---

## 技术栈与依赖

```
核心语言：  Python 3.14
数据处理：  pandas 2.x, fastparquet
可视化：    plotly 6.7, kaleido（静态导出）
Dashboard： streamlit 1.58
网络分析：  networkx 3.6（Louvain 社区检测、介数中心性、聚类系数）
其他：      numpy, base64, pathlib
```

**没有使用**：数据库、Spark、Dask、Redis、Docker。整个项目是单机 Python 脚本集合，所有分析在内存中完成。

---

## 数据流与工作流程

### 完整管道

```
原始 CSV（~3GB）         process_data.py          processed/（~1.3MB）
─────────────────  ────>  ───────────────  ────>  ──────────────────
Activity Logs            chunked read +            participant_summary
  (72 文件, 114M 行)      vectorized groupby       hourly_activity
CheckinJournal                                     daily_activity
FinancialJournal                                   venue_checkins
SocialNetwork                                      financial_summary
TravelJournal                                      daily_financial
Attributes/*.csv                                   social_network
Jobs.csv + Employers.csv                           travel_purpose_summary
Buildings.csv                                      job_summary
                                                   building_types
                                                   pubs, restaurants,
                                                   schools, apartments

                    ↓

processed/*.parquet     common.py             app.py（Dashboard）
─────────────────  ────>  ────────────  ────>  ──────────────────
全部 14 个文件            load_data()           Q1 人口特征
                          compute_network_      Q2 社交活动
                            metrics()           Q3 商业经济
                          make_q*_*()           Q4 城市概览
                          prepare_*()

                    ↓

processed/*.parquet     common.py             export_answer_sheet.py
─────────────────  ────>  ────────────  ────>  ───────────────────────
                         （同上）              生成 33 张 PNG 图表
                                              + 合成 index.htm
```

### 分析逻辑链路（Q1 → Q2 → Q3 → Q4）

```
Q1 人口基线
  ├─ 年龄结构 → Q2 年龄-连通性曲线（模式六）
  ├─ 兴趣组均匀 → Q2 社区检测预期（模式二）
  ├─ 家庭微型 → Q3 微型企业（发现一、发现四）
  └─ 教育-余额梯度 → Q3 工资分析（发现三）

Q2 社交网络
  ├─ 度分布重尾 → Q2 桥接个体（模式七）
  ├─ 场所偏好（餐饮主导）→ Q3 支出结构（发现二）
  ├─ 昼夜节律 → Q3 双周工资周期的消费节律
  └─ 场所集聚 → Q4 地图（图 4.4）

Q3 经济基础
  ├─ 微型雇主 → Q1 微型家庭（发现一）
  ├─ 休闲支出≈食品支出 → Q2 场所偏好 + 出行目的
  └─ 产业不可分类 → Q1 教育多样性

Q4 综合概览
  └─ 一页信息图（谁/如何生活/经济/场所）← Q1+Q2+Q3 交叉证据
```

---

## 关键架构决策

### 1. common.py 作为唯一分析引擎
**最初**：`app.py` 包含所有数据加载和图表生成逻辑（~2,000 行）。  
**现在**：`common.py` 抽取为共享层，`app.py` 和 `export_answer_sheet.py` 都导入它。  
**原因**：避免在两个消费者之间复制图表逻辑；确保 Dashboard 和 Answer Sheet 使用的数值完全一致。

### 2. 社交网络分析在内存中完成
网络指标（社区检测、中心性、聚类）在 `common.py` 的 `compute_network_metrics()` 中实时计算，不在 `process_data.py` 中预计算。  
**好处**：管道简单，输出文件小（160K 行而非全图序列化）。  
**代价**：首次加载 networkx 图分析需 10–30 秒（`@st.cache_data` 缓存后续命中）。

### 3. 所有图表数值动态计算
Dashboard 和 Answer Sheet 中的每个数字都从 `processed/*.parquet` 实时计算，不存在硬编码数值。  
**好处**：若原始数据更新（如 VAST 发布修正版），重新运行 `process_data.py` 后所有输出自动更新。

### 4. Answer Sheet 采用中文 + 分析推理格式
不同于官方英文模板的简单问答格式，本项目 Answer Sheet 增加了：
- 每个发现/模式后紧跟对应图表（"一图一析"）
- `🔍 分析思路` 框解释分析方法和推理链
- 跨问题交叉引用（"见图 X.Y"）
- Munzner (2009) 四层嵌套模型作为分析框架声明
- 三大板块分组（Q2：网络结构 → 行为时间 → 人口空间）

### 5. 不使用 Web 框架导出
静态 PNG 图表通过 `kaleido` 引擎直接从 Plotly figure 导出，不依赖 Playwright 或无头浏览器。

---

## 本阶段变更记录

**时间跨度**：2026-06-02（V2）→ 2026-06-10（V2.1）  
**核心主题**：从英文数据浏览器升级为中文学术分析报告 + 完整答题卷

### 一、架构重构（高影响）

| 变更 | 改前 | 改后 | 文件 |
|------|------|------|------|
| **抽取共享引擎** | `app.py` 包含全部逻辑（~2,000 行） | `common.py`（1,218 行）抽取数据加载/图表/网络分析；`app.py`（1,466 行）只负责页面渲染 | `common.py` + `app.py` |
| **创建静态导出器** | 不存在 | `export_answer_sheet.py`（910 行）用 kaleido 导出 33 张 PNG + 合成 `index.htm` | `export_answer_sheet.py`（新建） |

### 二、app.py 中文化与内容升级

| 变更 | 详情 |
|------|------|
| **全页面翻译** | Q1–Q4 全部页面标题、分析文字、图表标签翻译为学术中文 |
| **侧边栏导航** | 标题、导航选项、底部说明全部中文 |
| **分析框架声明** | 每页增加 Munzner (2009) 四层嵌套模型框（领域情境 → 数据抽象 → 视觉编码 → 图表设计） |
| **交叉引用** | 发现之间增加"见图 X.Y"交叉引用链接 Q1↔Q2↔Q3↔Q4 |
| **措辞风格** | 统一为学术报告语气（"特征""模式""发现""依据"），非数据浏览器描述 |

### 三、Answer Sheets/index.htm 完全重构

**第一轮**（中文化翻译）：将原英文模板 ~320 行全部翻译为中文，包括：
- 页面元数据（`lang="zh-CN"`、中文字体栈）
- 参赛信息、Q1–Q4 分析文本、Munzner 框架框
- 全部 33 张图表标题（"图 X.Y：..."）
- 合规摘要表、参考文献

**第二轮**（结构重组 + 分析推理注入）：
- **布局重构**：从"先文后图"改为"发现→图表→图注→分析思路"逐条穿插
- **分析思路框**：每个发现/模式后增加 `🔍 分析思路` 框（蓝灰色左边框），解释：
  - 为什么用这个图表类型（视觉编码选择理由）
  - 统计特征如何解读（均值 vs 中位数、LOWESS 趋势线、对数-对数轴等）
  - 该发现与上下文的逻辑关联（交叉引用 + 证据链）
  - 方法论优势与局限
- **Q2 板块化**：将 10 项模式组织为 A（网络结构属性）、B（行为与时间模式）、C（人口与空间关联）三大板块
- **图注增强**：每张图的标题从一句话扩展为包含轴含义、关键数值标注、视觉特征描述
- **样式系统**：新增 `.framework-box`、`.reasoning-box`、`.finding-label`、`.caption` 等 CSS 类

### 四、图表资产

| 产出 | 数量 | 路径 |
|------|------|------|
| Q1 图表 | 9 张 PNG | `Answer Sheets/VAST Challenge 2022 C1 Answer Sheet_files/chart_q1_*.png` |
| Q2 图表 | 11 张 PNG + 1 张 GIF | `.../chart_q2_*.png` + `chart_q2_12_hourly_animation.gif` |
| Q3 图表 | 9 张 PNG | `.../chart_q3_*.png` |
| Q4 图表 | 4 张 PNG（含地图） | `.../chart_q4_*.png` |
| **合计** | **33 张 + 1 张 GIF** | |

---

## 当前产出状态

### 已完成 ✅

| 任务 | 状态 | 说明 |
|------|------|------|
| 数据管道 | ✅ | `process_data.py` 正确处理全部原始 CSV → 14 个 parquet |
| Dashboard V1 → V2 升级 | ✅ | 从数据浏览器升级为分析报告（2026-06-02） |
| common.py 共享引擎 | ✅ | 数据加载、图表生成、网络分析统一抽离（2026-06-09） |
| export_answer_sheet.py | ✅ | 静态 PNG 导出 + index.htm 生成 |
| app.py 全中文化 | ✅ | Q1–Q4 + 侧边栏 + Munzner 框架框（2026-06-09） |
| Answer Sheet 中文化 | ✅ | 全 321 行翻译（2026-06-09） |
| Answer Sheet 结构重组 | ✅ | "一图一析"布局 + 分析思路 + 逻辑链（2026-06-10） |
| Q2 工作日/周末行为 | ✅ | 图 2.6（weekday_weekend 对比）+ 模式五分析 |
| Q4 信息图 | ✅ | 三小幅面图表 + 场所地图 + 四大板块描述 |
| 社交网络分析 | ✅ | Louvain 社区检测 + 度/介数/聚类系数 + 边权重分析 |
| 产业基础判定 | ✅ | 判定为"地方服务生态系统"——253 家微型企业、无主导产业 |
| 提交合规 | ✅ | Q1–Q3 各 ≤500 词 + ≤10 图，Q4 一页，总计 ~1,980 词 + 33 图 |

### 部分完成 ⚠️

| 任务 | 完成度 | 剩余工作 |
|------|--------|----------|
| Answer Sheet 图表内嵌 | 80% | `index.htm` 引用本地 PNG；若提交需确认路径可访问性 |
| Q2 模式证据 | 80% | 10 项模式均有量化指标 + LOWESS + 统计描述，部分模式的 p 值/置信区间未报告 |
| Q3 产业分类 | 60% | 28/253 家可分类（通过建筑-场所匹配）；89% 不可分类的雇主未进一步推断 |

---

## 待完成工作

### 高优先级 🔴

| 任务 | 说明 | 预估工作量 |
|------|------|-----------|
| **Answer Sheet 生成自动化** | 当前 `export_answer_sheet.py` 生成 PNG 图表，但 `index.htm` 的分析文字仍为手写。需要从分析结果中自动提取关键数值并填入模板，或至少确保 `export_answer_sheet.py` 生成的图表与 `index.htm` 引用的文件名完全一致 | 4–8 小时 |
| **Q2 统计检验加强** | 部分模式的证据依赖描述性统计（如模式五的峰值"17:00"、模式六的趋势线）。建议补充：(a) Kolmogorov-Smirnov 检验度分布的幂律拟合优度，(b) 工作日 vs 周末活动量的配对 t 检验，(c) 年龄-连通性 LOWESS 的 bootstrap 置信带 | 4–6 小时 |
| **Q3 产业分类细化** | 225 家"未分化商业企业"可能需要：(a) 通过雇主名称关键词推断类型，(b) 利用交易记录中的对方账户推断行业，(c) 结合位置数据做空间聚类分析 | 6–10 小时 |

### 中优先级 🟡

| 任务 | 说明 | 预估工作量 |
|------|------|-----------|
| **Q1 教育-年龄交叉分析** | 当前分别分析了年龄（发现一）和教育（发现二），但未做年龄×教育的双变量交叉。该分析可揭示不同年龄组的人力资本积累差异 | 2–4 小时 |
| **Q2 工作日/周末统计** | 图 2.6 已有视觉对比，但 `compute_weekend_metrics()` 中周末休闲时间的百分比变化需要从数据中验证（当前周末 Recreation "0%" 可能是计算错误，需排查） | 2–3 小时 |
| **Q4 信息图视觉增强** | 当前使用 streamlit 原生三栏布局 + HTML 信息框。可考虑：(a) 自定义 HTML/CSS 表格替代原生组件，(b) 图标/emoji 点缀关键指标，(c) 将小幅面图表增大至 300px | 3–5 小时 |
| **首次加载优化** | `@st.cache_data` 首次命中需 10–30 秒（networkx 社区检测）。考虑：(a) 将网络指标预计算写入 `processed/`，(b) 加载时展示进度条，(c) 懒加载非当前页的数据 | 2–4 小时 |

### 低优先级 🟢

| 任务 | 说明 |
|------|------|
| **配色方案统一** | 当前 Q1–Q4 使用混合调色板（plotly 默认 + 自定义），可统一为 3–4 色的主题调色板 |
| **图表增加注释** | 关键图表增加数据来源标注和统计检验结果注释 |
| **导航优化** | 可考虑"HUD 模式"单页滚动（report mode）替代当前 4-tab radio 导航 |
| **移动端响应式** | 当前针对桌面端设计，移动端 `max-width` 和图表缩放未适配 |
| **Playwright 替代方案** | Playwright 不支持 ubuntu 26.04，若需自动化截图，可迁移到 `selenium` 或使用 `kaleido` 导出（已有 `export_answer_sheet.py` 使用 kaleido） |

---

## 已知问题

| 问题 | 影响 | 修复方向 |
|------|------|----------|
| `buildingTypes` 数据拼写："Residental" 应为 "Residential" | 低（仅影响建筑类型标签显示） | 在 `process_data.py` 中做字符串替换 |
| 部分 venue 列名尾随空格（`"maxOccupancy "`） | 低（已处理） | `process_data.py` 已有 `.rename()` 修复 |
| `index.htm` 中 Q2 模式五周末 Recreation 显示为 "0%" | 中（数据可能有误） | 检查 `compute_weekend_metrics()` 的逻辑 |
| `@st.cache_data` 首次加载延迟 | 中（用户体验） | 见待完成工作中优先级第 4 项 |
| Playwright 不支持 ubuntu 26.04 | 低（当前用 kaleido 替代） | 等 Playwright 更新或迁移截图方案 |
| Q2 Fig 2.11 引用但图注写"10 images"而 Q2 实际有 11 张图 | 低（合规表已标注 11） | 统一措辞 |

---

## 给接手指南

### 如果你想……

#### **理解项目**
1. 先读本文件（你正在读的）
2. 读 [`CLAUDE.md`](CLAUDE.md) 了解数据源映射、app.py 架构、完整待办列表
3. 打开 `app.py`，运行 `streamlit run app.py`，在浏览器里逐页浏览 Q1→Q4
4. 打开 `Answer Sheets/index.htm` 在浏览器中查看最终提交物的渲染效果

#### **修改分析逻辑**
1. **只改图表样式** → 编辑 `common.py` 中的 `make_q*_*()` 函数
2. **改网络分析算法** → 编辑 `common.py` 中的 `compute_network_metrics()`
3. **改数据处理方式** → 编辑 `process_data.py`，重新运行后所有下游自动更新
4. **改页面布局/文字** → 编辑 `app.py` 对应的 Q-section 部分

#### **重新生成 Answer Sheet**
```bash
python3 export_answer_sheet.py
```
这会用 `common.py` 的分析逻辑重新生成全部 33 张 PNG 图表。然后手动检查 `index.htm` 中的分析文字是否需要同步更新（因为 `index.htm` 的分析文字是手写的，不会自动更新数值）。

#### **添加新的分析维度**
1. 如果需要新的聚合数据 → 在 `process_data.py` 中新增处理函数
2. 如果只是现有数据的新的可视化 → 在 `common.py` 中新增 `make_q*_newchart()` 函数
3. 在 `app.py` 对应页面中调用新图表
4. 同步更新 `index.htm`（增加图片引用和分析文字）

### 常见陷阱

- **路径问题**：`common.py` 中 `DATA_ROOT` 指向 `../VAST-Challenge-2022/VAST-Challenge-2022/`，如果原始数据放在别处需要修改这个常量
- **缓存问题**：修改 `common.py` 或 `process_data.py` 后，Streamlit 的 `@st.cache_data` 可能返回旧结果 → 在 Dashboard 侧边栏点"Clear Cache"或重启 app
- **图表数量限制**：VAST Challenge 规定每问 ≤10 张图。如果在 `app.py` 中加了新图但 Q2 已经有 11 张，提交时需按 10 张上限取舍（当前 Q2 11 张已超限 1 张）
- **文字不可硬编码**：`index.htm` 中所有数值（如均值、中位数）应与 `app.py` 实时计算值一致。修改 `process_data.py` 后务必重新运行 `export_answer_sheet.py` 并手动核对 `index.htm` 中的数字
- **kaleido 导出失败**：部分 plotly 图表类型（如动画、3D）kaleido 不支持。如需导出这类图表，用 `plotly.io.write_image()` 替代

### 提交前检查清单

- [ ] 运行 `python3 process_data.py` 确认无报错
- [ ] 运行 `streamlit run app.py` 确认 4 页渲染正常
- [ ] 运行 `python3 export_answer_sheet.py` 重新生成全部 PNG
- [ ] 浏览器打开 `Answer Sheets/index.htm` 确认所有图片加载正常
- [ ] 逐页核对 Q1–Q3 词数 ≤500、图表 ≤10、Q4 不超过一页
- [ ] 确认合规摘要表中的数字与实际一致
- [ ] 确认所有交叉引用（"见图 X.Y"）的图号正确
- [ ] 确认参赛信息（团队名称、成员、工时）填写完整
- [ ] 检查视频链接是否可访问（如允许发布视频设为"是"）

---

## 参考文献

- [VAST Challenge 2022 Official Site](https://vast-challenge.github.io/2022/)
- Munzner, T. "A Nested Model for Visualization Design and Validation." *IEEE TVCG*, 2009.
- Blondel, V. D. et al. "Fast unfolding of communities in large networks." *J. Stat. Mech.*, 2008.
- [Streamlit Documentation](https://docs.streamlit.io)
- [Plotly Python](https://plotly.com/python/)
- [NetworkX Documentation](https://networkx.org)
