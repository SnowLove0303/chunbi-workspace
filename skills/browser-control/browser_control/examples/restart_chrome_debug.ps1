# 找出带调试端口的 Chrome 进程（我启动的），保留用户正常 Chrome
Get-Process chrome -ErrorAction SilentlyContinue | ForEach-Object {
    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
    if ($cmd -and ($cmd.Contains("remote-debugging-port") -or $cmd.Contains("chrome_debug") -or $cmd.Contains("chrome_fresh_debug"))) {
        Write-Host "[$($_.Id)] REMOTE DEBUG CHROME - will restart"
        Write-Host "    Cmd: $($cmd.Substring(0, [Math]::Min(200, $cmd.Length)))"
    } else {
        Write-Host "[$($_.Id)] USER CHROME - keep running"
    }
}
