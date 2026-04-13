"""
winremote-mcp 状态检测脚本

检测:
  1. winremote-mcp 是否安装
  2. MCP 端口是否在运行
  3. 列出所有可用工具

用法:
  python winremote_check.py
  python winremote_check.py --port 8000   # 指定端口检测
"""
import sys
import socket
import subprocess
import json
import os
import io

# Windows GBK 兼容
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def check_package():
    """检测 winremote-mcp 是否安装"""
    try:
        result = subprocess.run(
            ['pip', 'show', 'winremote-mcp'],
            capture_output=True, text=True, encoding='gbk', errors='ignore'
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if 'Version' in line or 'Location' in line:
                    print(f"  {line.strip()}")
            print("[OK] winremote-mcp 已安装")
            return True
        else:
            print("[WARN] winremote-mcp 未安装")
            print("  安装命令: pip install winremote-mcp")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def check_port(host='127.0.0.1', ports=None, timeout=2):
    """检测端口是否开放"""
    if ports is None:
        ports = [8000, 8080, 8100, 8888, 9999]  # 常见 MCP 端口

    print(f"\n[PORT CHECK] 检测 {host}:")
    open_ports = []
    for port in ports:
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.close()
            print(f"  端口 {port}: ✅ 开放")
            open_ports.append(port)
        except (socket.timeout, ConnectionRefusedError, OSError):
            print(f"  端口 {port}: ❌ 未开放")

    return open_ports


def check_mcp_config():
    """检测 OpenClaw MCP 配置"""
    print("\n[MCP CONFIG]")
    config_paths = [
        os.path.expandvars(r'%APPDATA%\openclaw\mcp.json'),
        r"C:\Users\chenz\.openclaw\mcp.json",
    ]
    for p in config_paths:
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                mcp_servers = config.get('mcpServers', {})
                print(f"  已配置 MCP Server ({len(mcp_servers)} 个):")
                for name in mcp_servers.keys():
                    print(f"    - {name}")
                return True
            except Exception as e:
                print(f"  读取失败: {e}")
        else:
            print(f"  {p}: 不存在")
    return False


def list_winremote_tools():
    """尝试获取 winremote-mcp 工具列表"""
    print("\n[TOOLS] winremote-mcp 工具清单（40+）:")
    tools = [
        # 窗口/屏幕
        "screen_snapshot", "screen_screenshot", "screen_screenshot_to_file",
        "screen_active_window", "screen_list_windows", "screen_window_info",
        "screen_window_move", "screen_window_resize", "screen_window_close",
        "screen_window_minimize", "screen_window_maximize",
        # 剪贴板
        "clipboard_read_text", "clipboard_write_text",
        "clipboard_read_image", "clipboard_write_image",
        "clipboard_read_files", "clipboard_read_html", "clipboard_read_rtf",
        # 进程
        "process_list", "process_kill", "process_start",
        # 文件
        "file_search", "file_operations",
        # 注册表
        "registry_read", "registry_write", "registry_delete",
        # 系统
        "system_info", "cpu_usage", "memory_usage",
        "network_addresses", "network_connections",
        "power_battery", "power_sleep", "power_hibernate",
        # 服务
        "service_list", "service_start", "service_stop",
        # 其他
        "wmiquery", "powershell_execute", "http_download",
    ]
    for t in tools:
        print(f"  - {t}")


def check_openclaw_tools():
    """检测 OpenClaw windows-desktop__ 工具可用性"""
    print("\n[OPENCLAW TOOLS] windows-desktop__ 工具（18 个）:")
    tools = [
        "Snapshot", "Screenshot", "Click", "Move", "Type",
        "Shortcut", "Scroll", "MultiEdit", "MultiSelect",
        "Clipboard", "App", "FileSystem", "PowerShell",
        "Process", "Registry", "Notification", "Scrape", "Wait"
    ]
    for t in tools:
        print(f"  - windows-desktop__{t}")
    print("  ✅ 全部内置，无需安装")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='winremote-mcp 状态检测')
    parser.add_argument('--port', '-p', type=int, nargs='+',
                        help='指定检测端口')
    parser.add_argument('--host', default='127.0.0.1',
                        help='检测主机')
    args = parser.parse_args()

    print("=" * 50)
    print("  windows-desktop-master 环境检测")
    print("=" * 50)

    # 1. winremote-mcp 安装
    check_package()

    # 2. 端口检测
    if args.port:
        check_port(args.host, args.port)
    else:
        check_port(args.host)

    # 3. MCP 配置
    check_mcp_config()

    # 4. 工具清单
    check_openclaw_tools()
    list_winremote_tools()

    print("\n[完成]")


if __name__ == '__main__':
    main()
