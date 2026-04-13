; THS 同花顺下单流程 AHK 宏
; 用法: 运行此脚本，或从 pywinauto 调用
; 2026-04-13

#SingleInstance Force
SendMode("Input")
CoordMode("Mouse", "Screen")

; 快捷键: Ctrl+Shift+T 执行下单流程
^!t::
    RunTHSTrade()
return

RunTHSTrade() {
    ; 确保 THS 窗口活动
    if WinExist("ahk_exe hexin.exe") {
        WinActivate()
        Sleep, 300
    } else {
        MsgBox("THS 未运行，请先启动")
        return
    }

    ; 焦点到代码输入框（根据实际坐标调整）
    MouseClick, 1, 426, 137
    Sleep, 200

    ; 输入股票代码
    Send, 000001
    Sleep, 300

    ; Tab 到价格
    Send, {Tab}
    Sleep, 200

    ; 输入价格（示例：10.50）
    Send, 10.50
    Sleep, 200

    ; Tab 到数量
    Send, {Tab}
    Sleep, 200

    ; 输入数量
    Send, 100
    Sleep, 200

    ; 下单确认
    Send, {Enter}

    MsgBox("下单流程完成")
}

; 暂停脚本
^!p:: Suspend

; 终止脚本
^!x:: ExitApp
