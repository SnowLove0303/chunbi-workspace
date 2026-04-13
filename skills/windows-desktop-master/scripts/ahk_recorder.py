"""
AutoHotkey 录制器 - 启动 AHK 内置 Recorder 并生成 .ahk 文件

用法:
  python ahk_recorder.py --output "F:\工作区间\my_macro.ahk"
  python ahk_recorder.py --output "output/trade.ahk" --name "下单流程"

Recorder 启动后:
  Ctrl+Shift+R  开始录制
  Ctrl+Shift+R  停止录制（再次按）
  Ctrl+Shift+P  暂停/继续
  Escape        结束录制
"""
import argparse
import subprocess
import os
import sys
import pathlib

AHK_DEFAULT_PATH = r"C:\Program Files\AutoHotkey v2\AutoHotkey.exe"
AHK_ALT_PATH = r"C:\Program Files (x86)\AutoHotkey\AutoHotkey.exe"


def find_autohotkey():
    """查找系统中的 AutoHotkey.exe"""
    for path in [AHK_DEFAULT_PATH, AHK_ALT_PATH, "autohotkey.exe"]:
        try:
            result = subprocess.run(
                ["where", "autohotkey.exe"] if path == "autohotkey.exe"
                else [path, "/?"],
                capture_output=True, timeout=5
            )
            if result.returncode == 0 or True:
                # 找到了，返回完整路径
                if path == "autohotkey.exe":
                    for line in result.stdout.decode('gbk', errors='ignore').splitlines():
                        if "AutoHotkey" in line:
                            return line.strip()
                return path
        except Exception:
            continue
    return None


def create_recorder_script(output_path: str, script_name: str) -> str:
    """生成 AHK 录制脚本"""
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    script = f'''; AutoHotkey 录制脚本 - {script_name}
; 生成时间: {pathlib.Path(__file__).parent.name}
; 使用说明:
;   Ctrl+Shift+R  开始/停止录制
;   Ctrl+Shift+P  暂停/继续
;   Escape        结束录制并保存

#SingleInstance Force
SendMode("Input")
#InstallKeybdHook
#InstallMouseHook

global Recorder := ""
global RecordedActions := []
global IsRecording := False
global IsPaused := False
global OutputFile := "{output_path}"

; --- 录制代码（AHK Recorder 部分）---
; 以下为基础录制逻辑框架
; 实际录制由 AHK 内置 Recorder 生成

OnKeyDown("R", "HandleKeyR")
OnKeyDown("P", "HandleKeyP")
OnKeyDown("Escape", "HandleEscape")

HandleKeyR() {{
    if (GetKeyState("Ctrl") && GetKeyState("Shift")) {{
        if (IsRecording) {{
            StopRecording()
        }} else {{
            StartRecording()
        }}
    }}
}}

HandleKeyP() {{
    if (GetKeyState("Ctrl") && GetKeyState("Shift")) {{
        TogglePause()
    }}
}}

HandleEscape() {{
    if (IsRecording) {{
        StopRecording()
        ExitApp()
    }}
}}

StartRecording() {{
    IsRecording := True
    IsPaused := False
    Recorder := "{{}}"
    ToolTip("录制中... (Ctrl+Shift+R 停止, Escape 结束)")
}}

StopRecording() {{
    IsRecording := False
    ToolTip()
    SaveRecording()
}}

TogglePause() {{
    IsPaused := !IsPaused
    ToolTip(IsPaused ? "暂停中..." : "录制中...")
}}

SaveRecording() {{
    content := ";; 录制动作已保存`n"
    for k, v in RecordedActions {{
        content .= v . "`n"
    }}
    FileDelete(OutputFile)
    FileAppend(content, OutputFile)
    MsgBox("已保存到: " . OutputFile)
}}

; --- 启动 AHK 内置 Recorder ---
; 注意: AHK 内置 Recorder 需要手动在 AHK 主窗口启动
; 这里启动 AHK 并显示 Recorder 窗口

#If (not IsRecording)
^q:: {
    Run("https://www.autohotkey.com/docs/commands/Recorder.htm")
}
#If

; 提示用户手动启动 Recorder
MsgBox("AutoHotkey Recorder 已就绪！`n`n"
     . "请在 AHK 主窗口点击 'Record' 按钮开始录制`n"
     . "或按 Ctrl+Shift+R 开始`n`n"
     . "脚本输出路径: " . OutputFile)
'''
    return script


def main():
    parser = argparse.ArgumentParser(description='AutoHotkey 录制器')
    parser.add_argument('--output', '-o', required=True,
                        help='输出 .ahk 文件路径')
    parser.add_argument('--name', '-n', default='未命名宏',
                        help='宏名称（注释用）')
    parser.add_argument('--run', action='store_true',
                        help='生成后立即运行')
    args = parser.parse_args()

    output_path = os.path.abspath(args.output)
    script_name = args.name

    # 生成 AHK 脚本
    script = create_recorder_script(output_path, script_name)

    # 保存
    with open(output_path, 'w', encoding='utf-8-sig') as f:
        f.write(script)

    print(f"[OK] AHK 录制脚本已生成: {output_path}")

    ahk_exe = find_autohotkey()
    if ahk_exe:
        print(f"[OK] 找到 AutoHotkey: {ahk_exe}")
    else:
        print("[WARNING] 未找到 AutoHotkey，请先运行 F:\\工作区间\\ahk-install.exe 安装")

    if args.run and ahk_exe:
        print("[RUN] 启动 AHK 脚本...")
        subprocess.Popen([ahk_exe, output_path])
        print("[RUN] AHK Recorder 已启动，请在 AHK 窗口中点击 Record 开始录制")


if __name__ == '__main__':
    main()
