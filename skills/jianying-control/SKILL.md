# 剪映精准控制 Skill

通过 uiautomation 实现对剪映的精准 UI 控制，支持按名称、AutomationId、控件类型定位。

## 使用场景

- "点击剪映的导出按钮"
- "在素材库中找到名为'开场'的视频"
- "在文本轨道添加文字：Hello World'"
- "将视频片段拖到第3秒位置"

## 工作流程

```
用户请求 → AI 分析目标元素特征
              ↓
    ┌─────────────────────────────────────┐
    │ uiautomation UI 树遍历               │
    │ 搜索条件: Name / AutomationId / Type│
    └──────────────────┬──────────────────┘
                       ↓
    ┌─────────────────────────────────────┐
    │ 找到元素 → 获取 center 坐标          │
    └──────────────────┬──────────────────┘
                       ↓
    ┌─────────────────────────────────────┐
    │ desktop.click(center) 或 type()     │
    └─────────────────────────────────────┘
```

## 核心代码模板

### 查找并点击按钮

```python
import uiautomation as uia

def find_and_click(window_name, element_name, element_type='ButtonControl'):
    """按名称查找窗口中的元素并点击"""
    # 1. 找窗口
    win = uia.WindowControl(RegexName=f'.*{window_name}.*', Depth=1)
    if not win.Exists(maxSearchSeconds=5):
        return f"未找到窗口: {window_name}"
    
    # 2. 递归查找元素
    def find_element(parent, name, depth=0, max_depth=8):
        if depth > max_depth:
            return None
        try:
            if name.lower() in (parent.CachedName or '').lower():
                return parent
            for child in parent.GetCachedChildren():
                result = find_element(child, name, depth+1, max_depth)
                if result:
                    return result
        except:
            pass
        return None
    
    # 3. 找到并点击
    elem = find_element(win, element_name)
    if elem:
        rect = elem.BoundingRectangle
        x, y = rect.xcenter(), rect.ycenter()
        uia.Click(x, y)
        return f"已点击: {element_name} at ({x}, {y})"
    return f"未找到元素: {element_name}"
```

### 枚举窗口所有可交互元素

```python
def list_interactive_elements(window_name, max_count=100):
    """列出窗口中所有可交互元素"""
    win = uia.WindowControl(RegexName=f'.*{window_name}.*', Depth=1)
    if not win.Exists(maxSearchSeconds=5):
        return []
    
    elements = []
    def collect(node, depth=0, max_depth=6):
        if depth > max_depth or len(elements) >= max_count:
            return
        try:
            rect = node.BoundingRectangle
            visible = rect.width() > 3 and rect.height() > 3
            name = node.CachedName or ''
            ctype = node.CachedControlTypeName
            aid = node.CachedAutomationId or ''
            
            if visible and (name or aid):
                elements.append({
                    'name': name,
                    'type': ctype,
                    'aid': aid,
                    'depth': depth
                })
            
            for child in node.GetCachedChildren():
                collect(child, depth+1, max_depth)
        except:
            pass
    
    collect(win)
    return elements
```

## 剪映常用元素定位

| 操作 | 定位方式 |
|------|----------|
| 点击导出 | `ButtonControl(Name='导出', Depth=3)` |
| 添加素材 | `ButtonControl(Name='添加', Depth=3)` |
| 播放/暂停 | `ButtonControl(Name='播放', Depth=2)` 或 `ToggleButtonControl` |
| 文本输入 | `EditControl(Depth=3)` |
| 素材库面板 | `PaneControl(Name='素材库', Depth=2)` |

## 依赖

- `uiautomation` (已安装在 site-packages)
- `windows-mcp` (用于 OpenClaw 集成)

## 注意事项

1. **优先使用 AutomationId**：如果元素有 AID，比 Name 更可靠
2. **注意 Depth 限制**：太深会影响性能，太浅可能找不到
3. **处理缺失元素**：总是检查 `Exists()` 再操作
4. **坐标系**：uiautomation 返回的是屏幕绝对坐标
