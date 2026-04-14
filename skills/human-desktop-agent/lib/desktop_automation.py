"""
Desktop Automation - 桌面自动化基础功能
基于 pyautogui + pygetwindow
"""
import pyautogui
import pygetwindow as gw
from typing import List, Dict, Optional, Tuple


def screenshot(path: Optional[str] = None) -> str:
    """截取屏幕"""
    if path is None:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = f.name
    
    img = pyautogui.screenshot()
    img.save(path)
    return path


def click(x: int, y: int, button: str = 'left') -> Dict:
    """点击指定位置"""
    pyautogui.click(x=x, y=y, button=button)
    return {"status": "ok", "action": "click", "x": x, "y": y}


def move(x: int, y: int, duration: float = 0.5) -> Dict:
    """移动鼠标"""
    pyautogui.moveTo(x, y, duration=duration)
    return {"status": "ok", "action": "move", "x": x, "y": y}


def type_text(text: str, interval: float = 0.0) -> Dict:
    """输入文字"""
    pyautogui.typewrite(text, interval=interval)
    return {"status": "ok", "action": "type", "text": text}


def press_key(key: str) -> Dict:
    """按键"""
    pyautogui.press(key)
    return {"status": "ok", "action": "press", "key": key}


def scroll(clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> Dict:
    """滚动"""
    if x is not None and y is not None:
        pyautogui.scroll(clicks, x=x, y=y)
    else:
        pyautogui.scroll(clicks)
    return {"status": "ok", "action": "scroll", "clicks": clicks}


def get_active_window() -> Optional[Dict]:
    """获取当前活动窗口"""
    win = gw.getActiveWindow()
    if win is None:
        return None
    return {
        "title": win.title,
        "left": win.left,
        "top": win.top,
        "width": win.width,
        "height": win.height
    }


def list_windows() -> List[str]:
    """列出所有窗口标题"""
    try:
        windows = gw.getAllTitles()
        return [w for w in windows if w.strip()]
    except:
        return []


def activate_window(title: str) -> Dict:
    """激活指定窗口"""
    try:
        wins = gw.getWindowsWithTitle(title)
        if wins:
            wins[0].activate()
            return {"status": "ok", "action": "activate", "title": title}
        return {"status": "error", "reason": "window not found"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def find_image_on_screen(template_path: str, confidence: float = 0.8) -> Optional[Tuple[int, int]]:
    """
    在屏幕上查找图片位置
    
    Returns:
        (x, y) 中心坐标，或 None
    """
    try:
        import cv2
        import numpy as np
        
        # 截图
        screen = pyautogui.screenshot()
        screen_np = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
        
        # 读取模板
        template = cv2.imread(template_path)
        if template is None:
            return None
        
        # 模板匹配
        result = cv2.matchTemplate(screen_np, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= confidence:
            h, w = template.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            return (center_x, center_y)
        return None
        
    except Exception as e:
        print(f"find_image error: {e}")
        return None


if __name__ == "__main__":
    # 测试
    print("Active window:", get_active_window())
    print("\nAll windows:", list_windows())
