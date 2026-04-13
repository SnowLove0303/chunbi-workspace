"""
AutoHotkey 脚本执行器

用法:
  python ahk_runner.py "F:\工作区间\my_macro.ahk"
  python ahk_runner.py "F:\工作区间\my_macro.ahk" --compile   # 编译成 exe
  python ahk_runner.py "F:\工作区间\my_macro.ahk" --wait      # 等待执行完成
  python ahk_runner.py list                                      # 查看运行中的 AHK 进程
"""
import argparse
import subprocess
import os
import sys

AHK_PATHS = [
    r"C:\Program Files\AutoHotkey v2\AutoHotkey.exe",
    r"C:\Program Files (x86)\AutoHotkey\AutoHotkey.exe",
    "autohotkey.exe",
]


def find_ahk_exe():
    """查找系统中的 AutoHotkey.exe"""
    for p in AHK_PATHS:
        try:
            if os.path.exists(p):
                return p
        except Exception:
            continue
    # 尝试 PATH 中查找
    try:
        result = subprocess.run(['where', 'autohotkey.exe'],
                               capture_output=True, text=True, timeout=5)
        for line in result.stdout.strip().splitlines():
            if line.strip():
                return line.strip()
    except Exception:
        pass
    return None


def list_ahk_processes():
    """列出所有运行中的 AHK 进程"""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq AutoHotkey*.exe'],
            capture_output=True, text=True, encoding='gbk', errors='ignore'
        )
        lines = result.stdout.strip().splitlines()
        if len(lines) > 3:
            print("运行中的 AHK 进程:")
            for line in lines[3:]:
                print(f"  {line.strip()}")
        else:
            print("没有运行中的 AHK 进程")
    except Exception as e:
        print(f"[ERROR] {e}")


def kill_ahk_processes():
    """终止所有 AHK 进程"""
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'AutoHotkey.exe'],
                       capture_output=True)
        subprocess.run(['taskkill', '/F', '/IM', 'AutoHotkey64.exe'],
                       capture_output=True)
        print("[OK] 所有 AHK 进程已终止")
    except Exception as e:
        print(f"[ERROR] {e}")


def run_script(script_path: str, wait: bool = False,
               compile_exe: bool = False, exe_out: str = None):
    """执行 AHK 脚本"""
    ahk_exe = find_ahk_exe()
    if not ahk_exe:
        print("[ERROR] 未找到 AutoHotkey.exe")
        print("  请运行: F:\\工作区间\\ahk-install.exe")
        return False

    script_path = os.path.abspath(script_path)
    if not os.path.exists(script_path):
        print(f"[ERROR] 脚本不存在: {script_path}")
        return False

    if compile_exe:
        # 编译成 exe
        if exe_out:
            out_path = os.path.abspath(exe_out)
        else:
            out_path = script_path.replace('.ahk', '.exe')
        print(f"[COMPILE] {script_path} -> {out_path}")
        result = subprocess.run(
            [ahk_exe, "/js", script_path, "/exe", out_path],
            capture_output=True, text=True, encoding='gbk', errors='ignore'
        )
        if result.returncode == 0:
            print(f"[OK] 编译成功: {out_path}")
        else:
            print(f"[ERROR] 编译失败: {result.stderr}")
        return

    # 执行脚本
    print(f"[RUN] {script_path}")
    if wait:
        result = subprocess.run([ahk_exe, script_path],
                                capture_output=True, text=True)
        print(f"[DONE] 返回码: {result.returncode}")
    else:
        subprocess.Popen([ahk_exe, script_path])
        print(f"[OK] 已启动（后台运行）")


def main():
    parser = argparse.ArgumentParser(description='AutoHotkey 脚本执行器')
    parser.add_argument('script', nargs='?',
                        help='.ahk 脚本路径')
    parser.add_argument('--run', '-r', action='store_true',
                        help='运行脚本')
    parser.add_argument('--compile', '-c', action='store_true',
                        help='编译成 exe')
    parser.add_argument('--exe-out', '-o',
                        help='exe 输出路径')
    parser.add_argument('--wait', '-w', action='store_true',
                        help='等待执行完成')
    parser.add_argument('--kill', '-k', action='store_true',
                        help='终止所有 AHK 进程')
    parser.add_argument('--list', '-l', action='store_true',
                        help='列出运行中的 AHK 进程')
    args = parser.parse_args()

    if args.kill:
        kill_ahk_processes()
        return

    if args.list:
        list_ahk_processes()
        return

    if not args.script:
        parser.print_help()
        ahk = find_ahk_exe()
        print(f"\n[INFO] AutoHotkey: {'已找到' if ahk else '未安装'}")
        return

    run_script(args.script, wait=args.wait,
               compile_exe=args.compile, exe_out=args.exe_out)


if __name__ == '__main__':
    main()
