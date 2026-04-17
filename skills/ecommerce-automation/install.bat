@echo off
chcp 65001 >nul
echo ========================================
echo   1688 选品 + 拼多多运营自动化技能
echo   安装脚本
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [√] Python 已安装
python --version
echo.

REM 安装依赖包
echo [步骤 1/2] 安装 Python 依赖包...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [警告] 部分依赖安装失败，请检查网络连接
)

echo.
echo [步骤 2/2] 安装 Playwright 浏览器...
playwright install edge
if errorlevel 1 (
    echo [警告] Edge 浏览器安装失败，尝试安装 Chrome...
    playwright install chrome
)

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 下一步操作：
echo 1. 编辑 config.yaml 配置文件
echo 2. 运行：python main.py --help
echo.
pause
