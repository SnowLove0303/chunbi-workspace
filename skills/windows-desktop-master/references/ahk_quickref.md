# AutoHotkey v2 快速参考

> AHK v2 语法 | 下载: F:\工作区间\ahk-install.exe

---

## 基础语法

```ahk
; 注释
#SingleInstance Force   ; 单实例
SendMode("Input")       ; 发送模式
CoordMode("Mouse")      ; 鼠标坐标模式

; 变量
name := "value"
num := 123

; 控制流
if (value > 10) {
    MsgBox("OK")
} else {
    MsgBox("NO")
}

Loop 3 {
    MsgBox("循环" . A_Index)
}
```

---

## 常用命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `Click, x, y` | 点击坐标 | `Click, 100, 200` |
| `Click, x, y, 2` | 双击坐标 | `Click, 100, 200, 2` |
| `Send, text` | 发送文本 | `Send, Hello World` |
| `Send, {Enter}` | 发送按键 | `Send, {Tab}` |
| `Send, ^c` | Ctrl+C | `Send, ^v` (Ctrl+V) |
| `Sleep, ms` | 等待 | `Sleep, 500` |
| `MouseMove, x, y` | 移动鼠标 | `MouseMove, 100, 200` |
| `WinActivate, title` | 激活窗口 | `WinActivate, ahk_exe notepad.exe` |
| `WinWait, title` | 等待窗口 | `WinWait, 无标题` |
| `ControlClick, btn` | 点击控件 | `ControlClick, Button1` |
| `ControlSetText, text` | 设置控件文本 | `ControlSetText, Edit1, hello` |

---

## 热键

```ahk
; 普通热键
^j:: Send("Hello")          ; Ctrl+J

; 组合热键
#r:: Run("notepad.exe")      ; Win+R 运行
^!q:: ExitApp               ; Ctrl+Alt+Q 退出

; 修饰符
#  = Win
^  = Ctrl
!  = Alt
+  = Shift
```

---

## 循环

```ahk
; 固定次数
Loop 5 {
    Send("A_Index = " . A_Index)
    Sleep, 300
}

; 文件循环
for file in DirFiles("C:\temp\*.txt") {
    MsgBox(file.Name)
}
```

---

## 窗口操作

```ahk
; 等待窗口出现
WinWait("ahk_exe notepad.exe")
WinActivate()

; 获取窗口信息
hwnd := WinGetID("A")
title := WinGetTitle("A")
```

---

## Python 调用 AHK

```python
import subprocess

# 运行脚本（后台）
subprocess.Popen(['autohotkey.exe', r'F:\path\to\script.ahk'])

# 编译成 exe
subprocess.run([
    r'C:\Program Files\AutoHotkey v2\AutoHotkey.exe',
    '/js', 'script.ahk', '/exe', 'output.exe'
])

# 终止所有 AHK
subprocess.run(['taskkill', '/F', '/IM', 'AutoHotkey.exe'])
```
