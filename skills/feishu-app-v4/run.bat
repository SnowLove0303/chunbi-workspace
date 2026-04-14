@echo off
chcp 65001 >nul
echo ================================================
echo   飞书应用创建自动化技能 v4.0
echo ================================================
echo.

REM 检查虚拟环境
if not exist ".venv" (
    echo [错误] 虚拟环境不存在，请先运行 install.bat
    pause
    exit /b 1
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 检查 Chrome 是否在调试模式运行
echo [检查] 验证 Chrome 调试端口...
powershell -Command "try { $tcp = New-Object System.Net.Sockets.TcpClient('127.0.0.1', 9222); $tcp.Close(); echo '[成功] Chrome 调试端口已连接' } catch { echo '[错误] Chrome 未以调试模式运行'; echo '请先启动 Chrome 调试模式:'; echo '复制以下命令到 CMD 运行:'; echo ''; echo '"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Users\%USERNAME%\AppData\Local\Google\Chrome\User Data"'; echo ''; pause; exit 1 }"

if errorlevel 1 (
    exit /b 1
)

echo.
echo [提示] 请确保:
echo 1. Chrome 浏览器已在调试模式下运行
echo 2. 已在浏览器中扫码登录飞书账号
echo 3. 权限配置文件 json.md 路径正确
echo.

REM 运行主程序
echo [启动] 开始自动化流程...
echo.
python feishu_cdp_automation.py

if errorlevel 1 (
    echo.
    echo [错误] 程序执行失败
    echo 请查看日志文件获取详细信息
    pause
    exit /b 1
)

echo.
echo ================================================
echo   执行完成!
echo ================================================
echo.
echo 查看结果:
echo - 截图文件：.\screenshots\
echo - 日志文件：.\logs\
echo - 执行报告：.\logs\report_*.txt
echo.
pause
