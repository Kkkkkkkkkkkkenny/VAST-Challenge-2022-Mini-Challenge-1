# VAST Challenge 2022 — Mini-Challenge 1: EngageTown

> IEEE VAST Challenge 2022 Mini-Challenge 1 可视化分析解决方案

## 1. 项目概述

本项目针对 IEEE VAST Challenge 2022 Mini-Challenge 1 赛题，对虚构城市 EngageTown 的 1,011 名居民进行多维可视化分析。数据集包含 1.14 亿条活动日志，时间跨度 15 个月（2022.03–2023.05），涵盖居民人口属性、社交活动、商业经济和空间分布四大维度。

**团队**：王甬拓、周晨旭、孙瑞笙、张雅晨、杨哲瑞（大数据 2302）

---

## 2. 分析框架

采用 Munzner (2009) 四层嵌套模型作为分析框架，围绕四个核心问题展开：

| 问题 | 分析维度 | 图表数量 |
|------|----------|----------|
| Q1: 人口特征 | 年龄、教育、家庭、经济 | 9 张 |
| Q2: 社交模式 | 网络结构、时间节律、空间分布 | 12 张 |
| Q3: 产业经济 | 企业规模、财务流向、行业分类 | 9 张 |
| Q4: 城市概览 | 综合画像、场所地图 | 4 张 |

---

## 3. 核心发现

### Q1: 人口特征

EngageTown 以劳动年龄人口为主体（平均 39.1 岁），家庭规模小（户均 2.0 人），教育水平与经济状况正相关。人口结构形成"自我强化循环"——劳动人口支撑小微企业，就业机会吸引年轻劳动力流入，但老年人口占比极低，缺乏代际传承机制。

### Q2: 社交模式

识别出 10 项显著社交模式。社交网络呈现近似正态的度分布与强社区结构（28 个 Louvain 社区，模块度 Q=0.5194）的张力。餐厅、酒吧等餐饮场所签到占比 38.2%，是社区最重要的社交枢纽。活动高峰出现在傍晚 17:00–19:00，周末峰值后移约 2 小时。

### Q3: 产业经济

253 家雇主均为小微企业（2–9 人），构成分布式服务生态系统。年工资总额 $55.6M，时薪 $10.01–$40.86。89% 的雇主无法识别具体行业，反映产业结构高度同质化。高度分散化是抗风险能力的来源，但也带来工资天花板和创新困境。

### Q4: 综合概览

EngageTown 的核心特质是"小型均衡中的隐性脆弱"——人口-经济均衡、空间均衡、社交均衡并存，但代际断层、经济单一性、社交脆弱性是三个结构性风险。

---

## 4. 技术实现

### 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.11+ | 核心语言 |
| Pandas / fastparquet | 数据处理与存储 |
| NetworkX | 社交网络分析（Louvain 社区检测、中心性计算） |
| Plotly | 交互式可视化图表 |
| Streamlit | Web Dashboard 应用 |
| Kaleido | 静态 PNG 导出 |

### 数据处理流程

```
原始 CSV (~3GB)
    ↓ process_data.py
processed/*.parquet (14 文件, ~1.3MB)
    ↓ common.py (共享分析引擎)
    ├── app.py (Streamlit Dashboard)
    └── export_answer_sheet.py (PNG 导出 + HTML 合成)
```

---

## 5. 运行方法

### 环境要求

- Python 3.11+
- 约 4GB 磁盘空间（原始 CSV）

### 安装与运行

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 处理原始数据（首次运行，约 5-10 分钟）
# 需将 Datasets/ 目录置于项目同级
python3 process_data.py

# 启动 Dashboard
streamlit run app.py

# 生成静态 Answer Sheet（可选）
python3 export_answer_sheet.py
```

---

## 6. 项目结构

```
├── app.py                    # Streamlit Dashboard
├── common.py                 # 共享分析引擎
├── process_data.py           # 数据处理管道
├── export_answer_sheet.py    # 答题卷导出
├── requirements.txt          # Python 依赖
├── setup.sh / setup.bat      # 一键配置脚本
├── processed/                # 处理后的 parquet 文件
├── Answer Sheets/            # 答题卷 HTML + 33 张图表
├── 答辩.pptx                 # 答辩 PPT（含讲稿备注）
├── solution.pdf              # 结题文档
└── 贡献分配表.xlsx            # 组内贡献分配
```

---

## 7. 参考文献

1. Munzner, T. "A Nested Model for Visualization Design and Validation." *IEEE TVCG*, 15(6), 921–928, 2009.
2. Blondel, V. D. et al. "Fast unfolding of communities in large networks." *J. Stat. Mech.*, 2008.
3. [IEEE VAST Challenge 2022](https://vast-challenge.github.io/2022/)
