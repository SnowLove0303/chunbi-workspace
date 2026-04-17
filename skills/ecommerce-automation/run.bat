@echo off
chcp 65001 >nul
title 1688 选品 + 拼多多运营自动化技能

echo ========================================
echo   1688 选品 + 拼多多运营自动化技能
echo ========================================
echo.
echo 请选择要执行的操作：
echo.
echo [1] 执行全流程自动化
echo [2] 1688 智能选品
echo [3] 拼多多商品上架
echo [4] 订单处理
echo [5] 库存同步
echo [6] 生成销售报表
echo [7] 商品合规检测
echo [8] 查看帮助
echo [0] 退出
echo.
set /p choice=请输入选项 (0-8): 

if "%choice%"=="1" python main.py all
if "%choice%"=="2" python main.py select
if "%choice%"=="3" python main.py publish
if "%choice%"=="4" python main.py orders
if "%choice%"=="5" python main.py sync
if "%choice%"=="6" python main.py report
if "%choice%"=="7" python main.py compliance
if "%choice%"=="8" python main.py --help
if "%choice%"=="0" exit

echo.
pause
