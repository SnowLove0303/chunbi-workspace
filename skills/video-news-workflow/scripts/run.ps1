# Video News Workflow - 启动器
# 用法: 右键 "用 PowerShell 运行", 或加入任务计划程序

$ErrorActionPreference = "Continue"
$Script = "F:\openclaw1\.openclaw\workspace\skills\video-news-workflow\scripts\generate.py"

Write-Host "========================================"
Write-Host "  Video News Workflow"
Write-Host "  Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
Write-Host "========================================"
Write-Host ""

python $Script

Write-Host ""
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
