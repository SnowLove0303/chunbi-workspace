"""
pywinauto 桌面应用控制封装

用法:
  from pywinauto_helper import AppController, find_window, screenshot

  ctl = AppController(backend='win32')  # 或 'uia'
  ctl.launch(r'E:\ths\同花顺\hexin.exe')
  ctl.wait_window(title_re='.*同花顺.*', timeout=10)
  ctl.click_button('下单')
  ctl.type_into('Edit', '000001')
"""
import sys
import os
import time
import io

# Windows GBK 兼容
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pywinauto import Application, Desktop
from pywinauto.findwindows import find_window, find_windows
from pywinauto.mouse import move, click, double_click, right_click
from pywinauto.keyboard import send_keys
from pywinauto.timings import wait_until_passes, TimeoutError as PYWinautoTimeoutError

# 后端
BACKENDS = ['win32', 'uia']


class AppController:
    """pywinauto 应用控制器"""

    def __init__(self, backend: str = 'win32'):
        if backend not in BACKENDS:
            raise ValueError(f"backend 必须为 {BACKENDS} 之一")
        self.backend = backend
        self.app = None
        self.window = None

    # ─── 启动应用 ───
    def launch(self, path: str, timeout: int = 10) -> 'AppController':
        """启动应用并等待主窗口"""
        self.app = Application(backend=self.backend).start(path)
        print(f"[LAUNCH] {path}")
        time.sleep(1)
        return self

    def connect(self, title_re: str = None, process: int = None,
                timeout: int = 10) -> 'AppController':
        """连接到已运行的应用"""
        criteria = {}
        if title_re:
            criteria['title_re'] = title_re
        if process:
            criteria['process'] = process

        self.app = Application(backend=self.backend).connect(**criteria)
        self.window = self.app.window(**criteria)
        print(f"[CONNECT] {criteria}")
        return self

    def window_(self, title_re: str = None, **kwargs):
        """获取窗口对象"""
        if self.app is None:
            raise RuntimeError("请先 launch() 或 connect()")
        w = self.app.window(title_re=title_re, **kwargs)
        self.window = w
        return w

    # ─── 等待 ───
    def wait_window(self, title_re: str = None, timeout: int = 10,
                    visible: bool = True) -> 'AppController':
        """等待窗口出现"""
        start = time.time()
        last_err = None
        while time.time() - start < timeout:
            try:
                wins = find_windows(title_re=title_re, visible=visible)
                if wins:
                    hwnd = wins[0]
                    self.app = Application(backend=self.backend).connect(handle=hwnd)
                    self.window = self.app.window(handle=hwnd)
                    print(f"[WINDOW] 找到窗口 HWND={hwnd}")
                    return self
            except Exception as e:
                last_err = e
            time.sleep(0.5)
        raise RuntimeError(f"等待窗口超时 ({timeout}s): {last_err}")

    # ─── 控件操作 ───
    def print_controls(self):
        """打印所有可用控件（调试用）"""
        if self.window:
            print(self.window.print_control_identifiers())

    def click(self, spec, right: bool = False, double: bool = False):
        """
        点击控件
        spec: 控件名/类名/title，或坐标 (x, y)
        """
        if isinstance(spec, tuple):
            x, y = spec
            if right:
                right_click(coords=(x, y))
            elif double:
                double_click(coords=(x, y))
            else:
                click(coords=(x, y))
        else:
            try:
                ctrl = self.window[spec]
                if right:
                    ctrl.right_click()
                elif double:
                    ctrl.double_click()
                else:
                    ctrl.click()
                print(f"[CLICK] {spec}")
            except Exception as e:
                print(f"[WARN] 点击 '{spec}' 失败: {e}")

    def click_button(self, text_or_spec: str):
        """点击按钮"""
        try:
            btn = self.window.child_window(title=text_or_spec, found_index=0)
            btn.click()
            print(f"[BTN] {text_or_spec}")
        except Exception as e:
            print(f"[WARN] 点击按钮 '{text_or_spec}' 失败，尝试 type: {e}")
            send_keys('{Enter}')

    def type_into(self, spec: str, text: str, with_spaces: bool = True):
        """向输入框输入文本"""
        try:
            edit = self.window[spec]
            edit.set_edit_text(text, with_spaces=with_spaces)
            print(f"[TYPE] {spec} = '{text}'")
        except Exception as e:
            print(f"[WARN] 向 '{spec}' 输入文本失败: {e}")
            send_keys(text)

    def press(self, key: str):
        """发送按键"""
        key_map = {
            'tab': '{Tab}', 'enter': '{Enter}', 'esc': '{Esc}',
            'space': ' ', 'up': '{Up}', 'down': '{Down}',
            'left': '{Left}', 'right': '{Right}',
            'home': '{Home}', 'end': '{End}',
            'f1': '{F1}', 'f2': '{F2}', 'f3': '{F3}', 'f4': '{F4}',
        }
        k = key_map.get(key.lower(), key)
        send_keys(k)
        print(f"[KEY] {k}")

    def menu_select(self, path: str):
        """执行菜单（如 'File -> Open'）"""
        if self.window:
            self.window.menu_select(path)
            print(f"[MENU] {path}")

    def close(self):
        """关闭窗口"""
        if self.window:
            self.window.close()
            print("[CLOSE] 窗口已关闭")

    def minimize(self):
        if self.window:
            self.window.minimize()

    def maximize(self):
        if self.window:
            self.window.maximize()

    def restore(self):
        if self.window:
            self.window.restore()


# ──────────────────────────────────────────
# 独立工具函数
# ──────────────────────────────────────────

def find_window_hwnd(title_re: str = None, process: int = None, visible: bool = True):
    """查找窗口 HWND"""
    wins = find_windows(title_re=title_re, process=process, visible=visible)
    if wins:
        return wins[0]
    return None


def screenshot(window_hwnd=None, path='screenshot.png'):
    """截图（仅支持 Win32 后端）"""
    try:
        from pywinauto.screenshot import capture
        if window_hwnd:
            img = capture(handle=window_hwnd)
        else:
            img = capture()
        img.save(path)
        print(f"[SCREENSHOT] {path}")
        return path
    except Exception as e:
        print(f"[ERROR] 截图失败: {e}")
        return None


def list_processes(name_filter: str = None):
    """列出进程"""
    try:
        import psutil
        for p in psutil.process_iter(['pid', 'name']):
            try:
                if name_filter is None or name_filter.lower() in p.info['name'].lower():
                    print(f"  PID={p.info['pid']}  {p.info['name']}")
            except Exception:
                pass
    except ImportError:
        print("[ERROR] 需要 psutil: pip install psutil")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='pywinauto 桌面控制')
    parser.add_argument('--backend', default='win32',
                        choices=BACKENDS, help='pywinauto 后端')
    parser.add_argument('--list', '-l', help='列出进程（过滤名）')
    parser.add_argument('--print-controls', '-p', metavar='TITLE_RE',
                        help='打印窗口控件')
    args = parser.parse_args()

    if args.list:
        list_processes(args.list)

    if args.print_controls:
        try:
            ctl = AppController(backend=args.backend)
            ctl.connect(title_re=args.print_controls, timeout=5)
            ctl.print_controls()
        except Exception as e:
            print(f"[ERROR] {e}")
