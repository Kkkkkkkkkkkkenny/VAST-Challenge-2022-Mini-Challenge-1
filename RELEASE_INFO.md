# RELEASE_INFO — GitHub 上传准备记录

**生成日期**：2026-06-10  
**项目版本**：V2.1  
**目的**：记录为 GitHub 上传所做的全部准备工作和变更决策

---

## 一、操作概览

为将 EngageTown VAST Challenge 2022 MC1 项目上传至 GitHub，进行了以下操作：

1. **重写 `.gitignore`** — 从基础模板升级为全面的 Python 数据科学项目忽略规则
2. **更新 `README.md`** — 新增"GitHub 上传准备"章节，记录追踪/忽略策略和再生指南
3. **创建 `RELEASE_INFO.md`** — 本文件，记录完整变更清单
4. **打包项目** — 创建 `.zip` 压缩包，排除 gitignored 文件

---

## 二、.gitignore 变更详情

### 修改前（旧版 .gitignore，342 字节）

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
*.egg

# Virtual environments
venv/
.venv/
env/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store

# Processed data (too large, can be regenerated)
processed/

# Jupyter
.ipynb_checkpoints/

# Streamlit
.streamlit/secrets.toml

# Large data files
Datasets/
Answer Sheets/
BaseMap.png
*.pdf
```

### 修改后（新版 .gitignore）

```gitignore
# =============================================================================
# .gitignore — EngageTown VAST Challenge 2022 MC1
# =============================================================================

# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
*.egg
*.so
dist/
build/

# Virtual environments
venv/
.venv/
env/
.env
.venv-*

# IDE / Editor
.idea/
.vscode/
*.swp
*.swo
*~
*.sublime-*

# OS generated files
.DS_Store
.DS_Store?
._*
Thumbs.db
ehthumbs.db
Desktop.ini

# Claude Code session files (local only)
.claude/

# Jupyter
.ipynb_checkpoints/
*.ipynb

# Streamlit
.streamlit/secrets.toml

# 原始数据集（~3GB）
Datasets/

# 处理后的 Parquet 中间文件
processed/
*.parquet

# 测试与调试
*.log
*.tmp
.pytest_cache/
coverage.xml
.coverage
htmlcov/

# 其他
*.bak
*.orig
```

### 关键变更对照表

| 条目 | 旧版 | 新版 | 变更原因 |
|------|------|------|----------|
| `Answer Sheets/` | ❌ 忽略 | ✅ **追踪** | 答题卷 HTML + 33 张 PNG 是项目最终成果，非中间产物 |
| `BaseMap.png` | ❌ 忽略 | ✅ **追踪** | 如存在则为 Dashboard 所需的静态资源 |
| `*.pdf` | ❌ 忽略 | ✅ **追踪** | 项目无 PDF，不需此规则；如有文档 PDF 应追踪 |
| `.claude/` | ❌ 未覆盖 | ✅ **忽略** | Claude Code 会话文件，与代码无关 |
| `*.so` | ❌ 未覆盖 | ✅ **忽略** | 编译的 C 扩展 |
| `dist/` `build/` | ❌ 未覆盖 | ✅ **忽略** | Python 打包产物 |
| `.env` | ❌ 未覆盖 | ✅ **忽略** | 环境变量文件 |
| `Thumbs.db` | ❌ 未覆盖 | ✅ **忽略** | Windows 系统文件 |
| `*.log` `*.tmp` | ❌ 未覆盖 | ✅ **忽略** | 调试/临时文件 |
| `.pytest_cache/` | ❌ 未覆盖 | ✅ **忽略** | 测试缓存 |
| `*.bak` `*.orig` | ❌ 未覆盖 | ✅ **忽略** | 备份文件 |
| `*.parquet` | ❌ 未覆盖 | ✅ **忽略** | 额外安全措施，防止 parquet 泄露到仓库 |
| `*.ipynb` | ❌ 未覆盖 | ✅ **忽略** | Jupyter notebook（通常含大量输出） |
| `*.sublime-*` | ❌ 未覆盖 | ✅ **忽略** | Sublime Text 配置 |

---

## 三、上传文件清单

以下文件包含在发行包中（按 gitignore 规则筛选）：

### Python 源代码（4 个文件，~4,600 行）

| 文件 | 行数 | 大小 | 用途 |
|------|------|------|------|
| `app.py` | 1,466 | ~84 KB | Streamlit 4 页分析 Dashboard |
| `common.py` | 1,218 | ~52 KB | 共享分析引擎（SSOT） |
| `export_answer_sheet.py` | 910 | ~60 KB | 静态 PNG 导出 + Answer Sheet 合成 |
| `process_data.py` | 494 | ~20 KB | 数据管道：CSV → Parquet |

### 文档（3 个文件）

| 文件 | 说明 |
|------|------|
| `README.md` | 项目总览、快速上手、结构、变更记录、接手指南（含 GitHub 上传章节） |
| `CLAUDE.md` | 开发者指南：数据源映射、app.py 架构、待办、已知问题 |
| `RELEASE_INFO.md` | 本文件：GitHub 上传变更记录 |

### 配置文件（1 个文件）

| 文件 | 说明 |
|------|------|
| `.gitignore` | 忽略规则（见第二章） |

### 历史文档（2 个文件）

| 文件 | 说明 |
|------|------|
| `docs/superpowers/specs/2026-05-30-mc1-improvement-plan.md` | V2 改进计划 |
| `docs/superpowers/plans/2026-05-30-mc1-pipeline-fix.md` | 数据管道修复记录 |

### 答题卷资产（35 个文件，~4.4MB）

| 类别 | 数量 | 路径 |
|------|------|------|
| HTML | 1 | `Answer Sheets/index.htm` |
| Q1 图表 | 9 | `Answer Sheets/VAST Challenge 2022 C1 Answer Sheet_files/chart_q1_01~09.png` |
| Q2 图表 | 11 | `Answer Sheets/VAST Challenge 2022 C1 Answer Sheet_files/chart_q2_01~11.png` |
| Q2 动画 | 1 | `Answer Sheets/VAST Challenge 2022 C1 Answer Sheet_files/chart_q2_12_hourly_animation.gif` |
| Q3 图表 | 9 | `Answer Sheets/VAST Challenge 2022 C1 Answer Sheet_files/chart_q3_01~09.png` |
| Q4 图表 | 4 | `Answer Sheets/VAST Challenge 2022 C1 Answer Sheet_files/chart_q4_01~04.png` |

### 总计

| 指标 | 数值 |
|------|------|
| **追踪文件** | 46 个 |
| **Python 源代码行数** | ~4,600 行 |
| **文档行数** | ~900 行（README 453 + CLAUDE 114 + RELEASE_INFO + 2 份历史规划） |
| **HTML 行数** | ~548 行 |
| **图表数** | 33 张 PNG + 1 张 GIF |
| **发行包大小** | ~5MB（不含原始数据和中间产物） |

---

## 四、被排除的文件（不在发行包中）

| 路径 | 大小 | 排除原因 | 获取方式 |
|------|------|----------|----------|
| `Datasets/` | ~3GB | 原始 CSV，版权归 VAST Challenge 官方 | [vast-challenge.github.io/2022](https://vast-challenge.github.io/2022/) 下载 |
| `processed/` | ~1.3MB | 中间 Parquet，可由管道重新生成 | `python3 process_data.py` |
| `venv/` | ~500MB | Python 虚拟环境，机器相关 | 按 README 安装依赖 |
| `.claude/` | ~2MB | Claude 会话文件 | 不适用 |
| `__pycache__/` | ~50KB | Python 字节码缓存 | 自动生成 |

---

## 五、数据再生指南

从发行包恢复到完全可运行状态：

```bash
# 0. 解压发行包
unzip VAST-Challenge-2022-MC1-Release.zip
cd VAST-Challenge-2022-Mini-Challenge-1-master

# 1. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate       # Linux/macOS
venv\Scripts\activate          # Windows

# 2. 安装依赖
pip install pandas fastparquet plotly streamlit networkx kaleido

# 3. 下载原始数据
# 访问 https://vast-challenge.github.io/2022/
# 下载 Mini-Challenge 1 数据包
# 解压到 ../VAST-Challenge-2022/VAST-Challenge-2022/Datasets/

# 4. 运行数据管道（约 5-10 分钟）
python3 process_data.py

# 5. 启动 Dashboard
streamlit run app.py
# → 浏览器访问 http://localhost:8501

# 6. 查看答题卷
# 浏览器直接打开 Answer Sheets/index.htm
```

---

## 六、发行包信息

| 属性 | 值 |
|------|-----|
| 文件名 | `VAST-Challenge-2022-MC1-Release.zip` |
| 压缩格式 | ZIP (Deflate) |
| 生成日期 | 2026-06-10 |
| 项目版本 | V2.1 |
| 源码语言 | Python 3.14 |
| 许可证 | 未指定（学术项目） |

---

## 七、变更日志

```
2026-06-10  重写 .gitignore（新增 15+ 条规则，移除 Answer Sheets 忽略）
            新增加 README "GitHub 上传准备" 章节
            创建 RELEASE_INFO.md（本文件）
            生成发行包 .zip 压缩文件
```

---

*本文件与 README.md 互补：README 面向接手指南，RELEASE_INFO 面向 GitHub 上传审计。*
