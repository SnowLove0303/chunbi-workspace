"""查找 Chrome 调试端口"""
import subprocess, json

# Get Chrome processes with their command lines
procs = subprocess.run(
    ["powershell", "-Command",
     "Get-Process chrome | ForEach-Object { $cmd = (Get-CimInstance Win32_Process -Filter \"ProcessId=$($_.Id)\").CommandLine; [PSCustomObject]@{Id=$_.Id; Cmd=$cmd} } | ConvertTo-Json -Depth 2"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
try:
    data = json.loads(procs.stdout)
    if isinstance(data, dict):
        data = [data]
    for p in data:
        cmd = p.get("Cmd", "") or ""
        if "remote-debugging-port" in cmd or "inspector" in cmd:
            print(f"PID {p['Id']}: {cmd[:200]}")
        elif "feishu" in cmd.lower() or "lark" in cmd.lower():
            print(f"Feishu related PID {p['Id']}: {cmd[:200]}")
        else:
            # Show all Chrome processes (first 3 only)
            pass
    print(f"\nTotal Chrome processes: {len(data)}")
    print(f"\nAll Chrome processes (first 5):")
    for p in data[:5]:
        cmd = (p.get("Cmd") or "")[:150]
        print(f"  PID {p['Id']}: {cmd}")
except Exception as e:
    print(f"Error: {e}")
    print("Raw output:", procs.stdout[:500])
