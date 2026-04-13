# winremote-mcp 工具清单（40+）

> winremote-mcp v0.4.15 | GitHub: dddabtc/winremote-mcp

---

## 屏幕 / 窗口

| 工具 | 说明 |
|------|------|
| `screen_snapshot` | 截图（返回 base64） |
| `screen_screenshot` | 保存截图到文件 |
| `screen_screenshot_to_file` | 指定路径保存截图 |
| `screen_active_window` | 获取当前活动窗口 |
| `screen_list_windows` | 列出所有窗口 |
| `screen_window_info` | 获取窗口详细信息 |
| `screen_window_move` | 移动窗口位置 |
| `screen_window_resize` | 调整窗口大小 |
| `screen_window_close` | 关闭窗口 |
| `screen_window_minimize` | 最小化窗口 |
| `screen_window_maximize` | 最大化窗口 |

---

## 剪贴板

| 工具 | 说明 |
|------|------|
| `clipboard_read_text` | 读取剪贴板文本 |
| `clipboard_write_text` | 写入剪贴板文本 |
| `clipboard_read_image` | 读取剪贴板图片（base64） |
| `clipboard_write_image` | 写入图片到剪贴板 |
| `clipboard_read_files` | 读取剪贴板文件列表 |
| `clipboard_read_html` | 读取 HTML 格式 |
| `clipboard_read_rtf` | 读取 RTF 格式 |

---

## 进程

| 工具 | 说明 |
|------|------|
| `process_list` | 列出所有进程 |
| `process_kill` | 终止进程 |
| `process_start` | 启动进程 |

---

## 文件

| 工具 | 说明 |
|------|------|
| `file_search` | 搜索文件 |
| `file_operations` | 读/写/复制/移动/删除文件 |

---

## 注册表

| 工具 | 说明 |
|------|------|
| `registry_read` | 读取注册表值 |
| `registry_write` | 写入注册表 |
| `registry_delete` | 删除注册表键/值 |

---

## 系统信息

| 工具 | 说明 |
|------|------|
| `system_info` | 系统基本信息 |
| `cpu_usage` | CPU 使用率 |
| `memory_usage` | 内存使用情况 |
| `network_addresses` | 网络 IP 地址 |
| `network_connections` | 网络连接列表 |

---

## 电源

| 工具 | 说明 |
|------|------|
| `power_battery` | 电池状态 |
| `power_sleep` | 进入睡眠 |
| `power_hibernate` | 休眠 |

---

## 服务

| 工具 | 说明 |
|------|------|
| `service_list` | 列出 Windows 服务 |
| `service_start` | 启动服务 |
| `service_stop` | 停止服务 |

---

## 其他

| 工具 | 说明 |
|------|------|
| `wmiquery` | WMI 查询 |
| `powershell_execute` | 执行 PowerShell 命令 |
| `http_download` | HTTP 下载文件 |
| `get_clipboard` | 读取剪贴板（别名） |
| `notification` | 发送 Windows 通知 |
