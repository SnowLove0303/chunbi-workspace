"""端口检测脚本 - 浏览器精准控制闭环方案配套"""
import socket
import sys
import subprocess
import time
import platform
import os
import io

# Windows GBK 兼容：替换 emoji 为 ASCII
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace' if sys.stdout.encoding != 'utf-8' else 'strict')

def check_port(host, port, timeout=3):
    """检测端口是否开放"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def get_chrome_path():
    """获取 Chrome 路径"""
    system = platform.system()
    if system == "Windows":
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
    elif system == "Darwin":
        paths = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    else:
        paths = ["/usr/bin/google-chrome", "/usr/bin/chromium-browser"]

    for p in paths:
        if os.path.exists(p):
            return p
    return None

def launch_chrome_debug():
    """启动 Chrome 调试模式"""
    chrome_path = get_chrome_path()
    if not chrome_path:
        print("[X] 未找到 Chrome，请手动安装或指定路径")
        return False

    system = platform.system()
    if system == "Windows":
        subprocess.Popen(
            f'"{chrome_path}" --remote-debugging-port=9222 '
            f'--user-data-dir="{os.getenv("TEMP")}\\chrome_debug"',
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    else:
        subprocess.Popen(
            f'"{chrome_path}" --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_debug"',
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    print(f"[+] Chrome 启动中（调试端口 9222）...")
    time.sleep(3)

    if check_port("127.0.0.1", 9222):
        print("[+] Chrome 调试端口 9222 已就绪")
        return True
    else:
        print("[X] Chrome 调试端口启动失败")
        return False

def check_services():
    """检测所有依赖服务"""
    services = [
        ("Chrome CDP", "127.0.0.1", 9222),
        ("OpenClaw Gateway", "127.0.0.1", 18789),
    ]

    results = {}
    for name, host, port in services:
        status = check_port(host, port)
        results[name] = status
        status_icon = "[+]" if status else "[!]"
        print(f"{status_icon} {name} ({host}:{port})")

    return results

def main():
    print("=" * 50)
    print("[=] 端口预检")
    print("=" * 50)

    results = check_services()

    if not results.get("Chrome CDP"):
        print("\n[*] Chrome 未检测到，尝试启动...")
        if launch_chrome_debug():
            results["Chrome CDP"] = True

    print()
    if all(results.values()):
        print("[+] 所有端口就绪，可以开始执行工作流")
        return 0
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"[!] 未就绪: {', '.join(failed)}")
        print("   启动失败的服务需要手动启动后继续")
        return 1 if "Chrome CDP" in failed else 0

if __name__ == "__main__":
    sys.exit(main())
