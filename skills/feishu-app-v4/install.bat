@echo off
chcp 65001 >nul
echo ================================================
echo   飞书应用创建自动化技能 - 安装脚本
echo ================================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [信息] 检测到 Python 环境
python --version
echo.

REM 创建虚拟环境
echo [步骤 1/3] 创建虚拟环境...
if not exist ".venv" (
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo [成功] 虚拟环境创建完成
) else (
    echo [信息] 虚拟环境已存在
)
echo.

REM 激活虚拟环境并安装依赖
echo [步骤 2/3] 安装 Python 依赖包...
call .venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt -q

if errorlevel 1 (
    echo [警告] 部分依赖安装失败，尝试使用备用方案
    echo 正在安装 playwright (备用)...
    pip install playwright -q
)

echo [成功] 依赖安装完成
echo.

REM 初始化 Playwright (如果使用)
echo [步骤 3/3] 初始化浏览器驱动...
call .venv\Scripts\activate.bat
python -m playwright install chromium --with-deps 2>nul
if errorlevel 1 (
    echo [信息] Playwright 初始化跳过 (使用 CDP 模式)
)

echo.
echo ================================================
echo   安装完成!
echo ================================================
echo.
echo 下一步:
echo 1. 确保 Chrome 浏览器已安装
echo 2. 以调试模式启动 Chrome:
echo    "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
echo      --remote-debugging-port=9222 ^
echo      --user-data-dir="C:\Users\%USERNAME%\AppData\Local\Google\Chrome\User Data"
echo 3. 运行 run.bat 启动自动化脚本
echo.
pause
