@echo off
chcp 65001 >nul
echo =========================================
echo  VAST Challenge 2022 MC1 — 环境配置
echo =========================================

echo.
echo [1/4] 检查 Python 版本...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到 Python，请先安装 Python 3.11+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

echo [2/4] 创建虚拟环境...
if not exist "venv" (
    python -m venv venv
    echo 已创建 venv\
) else (
    echo venv\ 已存在，跳过创建
)

echo.
echo [3/4] 安装依赖包...
call venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo 依赖安装完成

echo.
echo [4/4] 检查数据状态...
if exist "processed\participant_summary.parquet" (
    echo processed\ 已存在
) else (
    echo processed\ 不存在，请运行: python process_data.py
)

echo.
echo =========================================
echo  配置完成！
echo =========================================
echo.
echo 启动 Dashboard:
echo   venv\Scripts\activate
echo   streamlit run app.py
echo   浏览器访问 http://localhost:8501
echo.
pause
