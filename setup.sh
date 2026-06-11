#!/bin/bash
# VAST Challenge 2022 MC1 — 一键环境配置脚本
# 用法: bash setup.sh

set -e

echo "========================================="
echo " VAST Challenge 2022 MC1 — 环境配置"
echo "========================================="

# 检查 Python 版本
echo ""
echo "[1/4] 检查 Python 版本..."
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "错误: 未找到 Python，请先安装 Python 3.11+"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  macOS: brew install python"
    echo "  Windows: 从 https://www.python.org/downloads/ 下载安装"
    exit 1
fi

PY_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oP '\d+\.\d+')
echo "  找到: $($PYTHON_CMD --version) ($PYTHON_CMD)"

# 检查版本 >= 3.11
PY_MAJOR=$(echo $PY_VERSION | cut -d. -f1)
PY_MINOR=$(echo $PY_VERSION | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]); then
    echo "错误: 需要 Python 3.11+，当前版本 $PY_VERSION"
    exit 1
fi

# 创建虚拟环境（可选）
echo ""
echo "[2/4] 创建虚拟环境..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo "  已创建 venv/"
else
    echo "  venv/ 已存在，跳过创建"
fi

# 激活虚拟环境
source venv/bin/activate 2>/dev/null || true
echo "  已激活虚拟环境"

# 安装依赖
echo ""
echo "[3/4] 安装依赖包..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "  依赖安装完成"

# 检查 processed/ 目录
echo ""
echo "[4/4] 检查数据状态..."
if [ -d "processed" ] && [ "$(ls -A processed/*.parquet 2>/dev/null)" ]; then
    FILE_COUNT=$(ls processed/*.parquet 2>/dev/null | wc -l)
    echo "  processed/ 已存在（$FILE_COUNT 个 parquet 文件）"
else
    echo "  processed/ 不存在或为空"
    if [ -d "../VAST-Challenge-2022/VAST-Challenge-2022/Datasets" ] || [ -d "Datasets" ]; then
        echo "  检测到原始数据，是否运行数据处理管道？(y/n)"
        read -r ANSWER
        if [ "$ANSWER" = "y" ] || [ "$ANSWER" = "Y" ]; then
            echo "  运行 process_data.py..."
            $PYTHON_CMD process_data.py
        else
            echo "  跳过。稍后运行: $PYTHON_CMD process_data.py"
        fi
    else
        echo "  未检测到原始数据 Datasets/"
        echo "  请从 https://vast-challenge.github.io/2022/ 下载数据"
        echo "  放置到项目同级目录的 Datasets/ 下"
    fi
fi

echo ""
echo "========================================="
echo " 配置完成！"
echo "========================================="
echo ""
echo "启动 Dashboard:"
echo "  source venv/bin/activate"
echo "  streamlit run app.py"
echo "  浏览器访问 http://localhost:8501"
echo ""
echo "生成 Answer Sheet（需要 Chrome）:"
echo "  python3 export_answer_sheet.py"
echo ""
