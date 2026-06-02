# MC1 Dashboard — 改进计划与进度追踪

> 初始状态 (2026-05-30)：Dashboard 是数据浏览工具（展示分布图、统计指标）
> 当前状态 (2026-06-02)：V2 分析报告 — Q1-Q4 均有分析结论和量化证据，待生成 Answer Sheet 提交

---

## 进度总览

| Phase | 内容 | 状态 | 备注 |
|---|---|---|---|
| Phase 1 | 数据处理增强 | ✅ 完成 | 社交网络分析在 app.py 内用 cache 实现，未改 process_data.py |
| Phase 2 | Q1 人口画像 | ✅ 完成 | 5 个 Finding + 交叉分析 + 结论 |
| Phase 3 | Q2 社交活动 | ✅ 基本完成 | 10 个 Pattern，部分证据需加强 |
| Phase 4 | Q3 商业经济 | ✅ 完成 | 识别为小型服务经济，5 个 Finding |
| Phase 5 | Q4 城镇总结 | ✅ 基本完成 | 三栏信息图 + 地图，可进一步视觉优化 |
| Phase 6 | 整体打磨 | ⏳ 未开始 | 配色/排版/注释 |

---

## 已完成工作详情

### Phase 1: 数据处理增强 ✅
- [x] Task 1: 社交网络图分析 — Louvain 社区检测（28 社区, modularity 0.52）、betweenness centrality、clustering coefficient
- [x] Task 2: 时间序列聚合 — 小时级活动模式分析（hourly_activity 已存在于 processed/）
- [x] Task 3: 交叉分析 — 年龄 × 社交度、教育 × 收入（在 app.py `compute_cross_analysis()`）
- [ ] Task 4: 场馆关联分析 — 未实施（签到序列 → 场馆共现、热门路线）

### Phase 2: Q1 人口画像 ✅
- [x] 提炼 5 个关键人口特征（年龄结构/教育经济/家庭结构/兴趣分布/财务健康）
- [x] 每个 Finding 有分析文字框 + 配套图表
- [x] 底部综合结论（Who Lives in EngageTown?）
- [ ] 可改进：年龄-教育交叉分析图、收入分位数分析

### Phase 3: Q2 社交活动 ✅
已识别的 10 个模式：
1. [x] 度分布幂律特征
2. [x] 强社区结构（28 社区）
3. [x] 高局部聚类
4. [x] 场馆类型偏好（Apartment/Workplace/Restaurant/Pub）
5. [x] 昼夜活动节律
6. [x] 年龄与社交关联
7. [x] 关键桥梁人物
8. [x] 交互频率异质性
9. [x] 社交/娱乐出行主导
10. [x] 场馆地理聚类

需加强的项：
- [ ] Pattern 5: 补充工作日 vs 周末差异（需提取 day-of-week）
- [ ] 部分模式增加统计检验（如度分布的幂律拟合优度）
- [ ] Pattern 1: 加入 Gini 系数或更精确的幂律指数估计

### Phase 4: Q3 商业经济 ✅
核心发现：**小型服务经济** — 253 家微型企业（2-9 人），无大型雇主。
- [x] 雇主规模分布分析
- [x] 财务流结构（工资收入 vs 住房/娱乐/食物支出）
- [x] 工资分布与雇主规模交叉
- [x] 建筑类型与商业空间利用率
- [x] 交易模式分析（高频小额 vs 低频大额）
- [ ] 可改进：按 employer 名称/位置推断行业细分

### Phase 5: Q4 城镇总结 ✅
- [x] 渐变横幅 + 关键指标行
- [x] 三栏布局（Who We Are / How We Live / Our Economy）
- [x] 迷你图表 + 地图标注
- [x] 底部一句话总结
- [ ] 可改进：信息图更视觉化（自定义 HTML/CSS），减少字数

---

## 剩余工作

### 阻塞项（提交前必须完成）

1. **Answer Sheet 生成**
   - MC1 最终提交是 `index.htm`（Answer Sheet HTML）
   - 需要：每个 Q 选取 ≤10 张静态图表 + ≤500 字英文答案
   - 方案 A：从 app.py 中手动截图 + 写作答案文字
   - 方案 B：写脚本导出 Plotly 图为 PNG + 自动生成 HTML
   - 推荐方案 B，可新增 `generate_answer_sheet.py`

2. **答案文字撰写**
   - 当前 app.py 中的分析框是英文 bullet point 风格
   - 需要凝练为 500 字以内的连贯段落（每个 Q）
   - Q2 需要精确列出 10 个模式（编号 1-10）

### 增强项（提升分析质量）

3. **Q2 工作日 vs 周末分析**
   - `daily_activity.parquet` 有 day 列，可加入 day-of-week
   - 对比周末和工作日的签到/社交模式差异

4. **Q3 产业细分**
   - 如果能从原始数据中获得 employer 名称/地址
   - 结合 buildingType 推断具体行业（零售/餐饮/教育/医疗等）

5. **数值稳定性**
   - 首次加载时 networkx 计算需 10-30 秒
   - 可考虑将 `net_metrics` 也预计算并保存为 parquet

### 打磨项

6. **配色统一** — 当前 Q1-Q4 使用不同调色板（Blues/Greens/Reds）
7. **图表标注** — 增加数据来源和统计注释
8. **响应式** — 当前用 `st.columns()` 固定列数，移动端效果差

---

## 数据关键发现速查

| 指标 | 数值 | 来源 |
|---|---|---|
| 人口 | 1,011 | participant_summary |
| 平均年龄 | 39.1 岁 | participant_summary |
| 家庭规模 | 2.0 人 | participant_summary |
| 有孩比例 | 29.8% | participant_summary |
| 兴趣组 | 10 组 (A-J)，均匀分布 | participant_summary |
| 社交边数 | 80,483 | social_network |
| 社区数 | 28 (modularity 0.52) | networkx Louvain |
| 年薪总额 | $55.6M | financial_summary |
| 雇主数 | 253 (均 5.2 人，最大 9 人) | job_summary |
| 平均时薪 | $19.22 ($10-$41) | job_summary |
| 最大支出 | Shelter $9.0M | financial_summary |
| 建筑类型 | 住宅 526 / 商业 512 / 学校 4 | building_types |

---

## 开发指南

### 新增社交网络指标
如需计算新的图指标，在 `app.py` 的 `compute_network_metrics()` 中添加，利用 `@st.cache_data` 自动缓存。如需持久化为 parquet：
```python
# 可在 process_data.py 的 main() 末尾添加
net_metrics["degree"].to_parquet(OUTPUT / "social_degree.parquet")
```

### 测试
```bash
# 启动 app
streamlit run app.py

# 检查数据
python3 -c "
import pandas as pd
from pathlib import Path
for f in Path('processed').glob('*.parquet'):
    df = pd.read_parquet(f)
    print(f'{f.name}: {len(df)} rows, {list(df.columns[:3])}')
"

# 重新处理数据
python3 process_data.py
```
