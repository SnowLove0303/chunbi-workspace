#!/usr/bin/env python3
"""
快速打开调兵系统 Web 界面
用法: python3 tiao-bing-open-web.py [copaw|openclaw|opencode|all]
"""

import subprocess
import argparse
import time
import sys

OPENCODE_WEB = r"F:\AI\opencode\opencode-cli.exe"
OPENCLAW_WEB_PORT = 18789  # OpenClaw gateway web port

def open_url(url):
    """Open URL in Windows default browser."""
    # Try wslview first, fall back to PowerShell
    try:
        subprocess.run(['wslview', url], capture_output=True, timeout=10)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: use PowerShell Start
    script = f'Start-Process "{url}"'
    subprocess.run(
        ['/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe', '-NoProfile', '-Command', script],
        capture_output=True, timeout=10
    )
    return True

def open_windows_exe(path, args=None):
    """Open a Windows executable."""
    cmd = [path]
    if args:
        cmd.extend(args)
    subprocess.Popen(
        cmd,
        cwd='/mnt/c',
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return True

def open_opencode_web():
    """Open OpenCode web UI."""
    print("Opening OpenCode Web UI...")
    subprocess.Popen(
        [OPENCODE_WEB, 'web', '--hostname', '127.0.0.1', '--port', '4096'],
        cwd='/mnt/c',
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)
    open_url('http://127.0.0.1:4096')
    print("OpenCode Web: http://127.0.0.1:4096")
    return True

def open_openclaw_web():
    """Open OpenClaw web interface."""
    print("Opening OpenClaw Web UI...")
    open_url(f'http://127.0.0.1:{OPENCLAW_WEB_PORT}')
    print(f"OpenClaw Web: http://127.0.0.1:{OPENCLAW_WEB_PORT}")
    return True

def open_copaw_web():
    """Open CoPaw web interface."""
    print("Opening CoPaw Web UI...")
    # CoPaw doesn't have a web UI by default, but we can open the workspace folder
    # or the API docs if available
    # Let's try to find if there's a web port
    import urllib.request
    try:
        # Check if copaw has any web interface
        urllib.request.urlopen('http://127.0.0.1:8088', timeout=2)
        open_url('http://127.0.0.1:8088')
        print("CoPaw: http://127.0.0.1:8088")
    except:
        # No web UI, just open the workspace
        script = "Start-Process 'F:\\copaw'"
        subprocess.run(
            ['/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe', '-NoProfile', '-Command', script],
            capture_output=True, timeout=10
        )
        print("CoPaw workspace opened in Explorer")

    # Open CoPaw workspaces folder
    script = "Start-Process 'F:\\copaw\\workspaces'"
    subprocess.run(
        ['/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe', '-NoProfile', '-Command', script],
        capture_output=True, timeout=10
    )
    return True

def open_all():
    print("Opening all web interfaces...\n")
    open_opencode_web()
    time.sleep(1)
    open_openclaw_web()
    time.sleep(1)
    open_copaw_web()
    print("\nAll opened.")

def main():
    parser = argparse.ArgumentParser(description='快速打开调兵系统 Web 界面')
    parser.add_argument('target', nargs='?', default='all',
                        choices=['copaw', 'openclaw', 'opencode', 'all'],
                        help='目标系统 (默认: all)')
    args = parser.parse_args()

    if args.target == 'copaw':
        open_copaw_web()
    elif args.target == 'openclaw':
        open_openclaw_web()
    elif args.target == 'opencode':
        open_opencode_web()
    elif args.target == 'all':
        open_all()

if __name__ == '__main__':
    main()
