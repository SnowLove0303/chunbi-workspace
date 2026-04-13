# 杀掉所有 Chrome
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 用用户真实 profile 启动 Chrome，带调试端口
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$userDataDir = "C:\Users\chenz\AppData\Local\Google\Chrome\User Data"
$debugPort = 9222

Start-Process -FilePath $chromePath -ArgumentList @(
    "--remote-debugging-port=$debugPort",
    "--user-data-dir=`"$userDataDir`"",
    "--no-first-run",
    "--no-default-browser-check"
) -WindowStyle Normal

Start-Sleep -Seconds 5

# 验证端口
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:$debugPort/json/version" -TimeoutSec 5
    Write-Host "Chrome started successfully on port $debugPort"
    Write-Host $response.Content
} catch {
    Write-Host "Chrome may not have started correctly: $_"
}
