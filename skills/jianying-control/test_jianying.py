"""
剪映控制测试脚本
测试 uiautomation 能否准确识别剪映的 UI 元素
"""
import uiautomation as uia
import sys
import time

def find_jianying_window():
    """找到剪映窗口"""
    # 尝试多种窗口名称
    patterns = [
        '剪映',
        'JianYing',
        'CapCut',
    ]
    
    for pattern in patterns:
        win = uia.WindowControl(RegexName=f'.*{pattern}.*', Depth=1)
        if win.Exists(maxSearchSeconds=3):
            print(f'✓ Found window with pattern: {pattern}')
            print(f'  Name: {win.Name}')
            print(f'  ClassName: {win.ClassName}')
            print(f'  Handle: {hex(win.NativeWindowHandle)}')
            return win
    
    return None

def dump_ui_tree(control, depth=0, max_depth=5, max_count=150):
    """递归打印 UI 树"""
    if depth > max_depth:
        return []
    
    elements = []
    try:
        children = control.GetCachedChildren()
        for child in children:
            try:
                rect = child.CachedBoundingRectangle
                visible = rect.width() > 3 and rect.height() > 3
                
                if visible:
                    name = child.CachedName or ''
                    ctype = child.CachedControlTypeName
                    aid = child.CachedAutomationId or ''
                    cls = child.CachedClassName or ''
                    
                    # 过滤掉空白元素
                    if name.strip() or aid:
                        indent = '  ' * depth
                        elem_info = f'{indent}[{len(elements):3d}] {ctype:25} | {name[:40]:40} | AID:{aid[:25]:25} | {cls[:20]}'
                        elements.append(elem_info)
                        print(elem_info)
                    
                    # 递归遍历子元素
                    child_elements = dump_ui_tree(child, depth+1, max_depth, max_count - len(elements))
                    elements.extend(child_elements)
                    
            except Exception as e:
                pass
    except Exception as e:
        print(f'Error at depth {depth}: {e}')
    
    return elements

def find_element_by_name(parent, name_pattern, max_depth=6):
    """按名称查找元素"""
    results = []
    
    def search(node, depth=0):
        if depth > max_depth:
            return
        try:
            name = node.CachedName or ''
            if name_pattern.lower() in name.lower():
                rect = node.CachedBoundingRectangle
                results.append({
                    'name': name,
                    'type': node.CachedControlTypeName,
                    'aid': node.CachedAutomationId or '',
                    'cls': node.CachedClassName or '',
                    'rect': rect,
                    'center': (rect.xcenter(), rect.ycenter()) if rect.width() > 0 else None,
                    'depth': depth
                })
            
            for child in node.GetCachedChildren():
                search(child, depth+1)
        except:
            pass
    
    search(parent)
    return results

def find_element_by_aid(parent, aid_pattern, max_depth=6):
    """按 AutomationId 查找元素"""
    results = []
    
    def search(node, depth=0):
        if depth > max_depth:
            return
        try:
            aid = node.CachedAutomationId or ''
            if aid_pattern.lower() in aid.lower():
                rect = node.CachedBoundingRectangle
                results.append({
                    'name': node.CachedName or '',
                    'type': node.CachedControlTypeName,
                    'aid': aid,
                    'cls': node.CachedClassName or '',
                    'rect': rect,
                    'center': (rect.xcenter(), rect.ycenter()) if rect.width() > 0 else None,
                    'depth': depth
                })
            
            for child in node.GetCachedChildren():
                search(child, depth+1)
        except:
            pass
    
    search(parent)
    return results

def main():
    print('=' * 80)
    print('剪映 UI 识别测试')
    print('=' * 80)
    
    # 1. 找窗口
    print('\n[1] 查找剪映窗口...')
    win = find_jianying_window()
    
    if win is None:
        print('\n❌ 未找到剪映窗口！请确保剪映已打开。')
        print('\n提示: 你可以运行以下命令启动剪映:')
        print('  Start-Process \"C:\\Program Files\\CapCut\\CapCut.exe\"')
        return
    
    # 2. 列出所有 UI 元素
    print('\n[2] UI 元素树:')
    print('-' * 80)
    all_elements = dump_ui_tree(win, 0, 5)
    print('-' * 80)
    print(f'共找到 {len(all_elements)} 个可见元素')
    
    # 3. 测试搜索功能
    print('\n[3] 测试搜索功能:')
    
    # 搜索包含"导出"的元素
    print('\n  搜索包含"导出"的元素:')
    export_results = find_element_by_name(win, '导出')
    for r in export_results[:10]:
        center = r['center']
        print(f'    - {r["type"]} | {r["name"]} | AID:{r["aid"]} | 坐标:({center[0]},{center[1]})')
    
    # 搜索包含"按钮"的元素
    print('\n  搜索包含"添加"的元素:')
    add_results = find_element_by_name(win, '添加')
    for r in add_results[:10]:
        center = r['center']
        print(f'    - {r["type"]} | {r["name"]} | AID:{r["aid"]} | 坐标:({center[0]},{center[1]})')
    
    # 4. 导出所有按钮
    print('\n[4] 所有按钮控件:')
    buttons = []
    def find_buttons(node, depth=0, max_depth=6):
        if depth > max_depth:
            return
        try:
            if node.CachedControlTypeName == 'ButtonControl':
                rect = node.CachedBoundingRectangle
                if rect.width() > 5:
                    name = node.CachedName or '(无名称)'
                    aid = node.CachedAutomationId or ''
                    buttons.append({
                        'name': name,
                        'aid': aid,
                        'center': (rect.xcenter(), rect.ycenter()),
                        'depth': depth
                    })
            for child in node.GetCachedChildren():
                find_buttons(child, depth+1, max_depth)
        except:
            pass
    find_buttons(win)
    
    for b in buttons[:30]:
        print(f'    - [{b["depth"]}] {b["name"][:40]:40} | AID:{b["aid"][:25]} | 坐标:({b["center"][0]},{b["center"][1]})')
    
    print(f'\n共找到 {len(buttons)} 个按钮')

if __name__ == '__main__':
    main()
