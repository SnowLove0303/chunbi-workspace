"""
Playwright CDP 客户端 - 连接到已有 Chrome（端口 9222）
所有交互操作通过这个 Client 进行。
"""
from playwright.sync_api import sync_playwright, Playwright
from typing import Optional, Dict, Any, List
import json, time, os

DEFAULT_CDP_URL = "http://127.0.0.1:9222"
DEFAULT_TIMEOUT = 30000  # ms


class BrowserClient:
    """复用 Chrome 调试端口的 Playwright 客户端"""

    def __init__(self, cdp_url: str = DEFAULT_CDP_URL, headless: bool = False):
        self.cdp_url = cdp_url
        self.headless = headless
        self._pw: Optional[Playwright] = None
        self._browser = None
        self._page = None

    def __enter__(self):
        self._pw = sync_playwright().start()
        # 连接已有 Chrome，而不是启动新的
        self._browser = self._pw.chromium.connect_over_cdp(self.cdp_url)
        # 默认上下文第一个页面
        contexts = self._browser.contexts
        if contexts:
            self._page = contexts[0].pages[0] if contexts[0].pages else contexts[0].new_page()
        else:
            self._page = self._browser.new_page()
        return self

    def __exit__(self, *args):
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    @property
    def page(self):
        return self._page

    # ──────────────────────────────────────────
    # 原子操作
    # ──────────────────────────────────────────

    def nav(self, url: str, wait_until: str = "load", timeout: int = DEFAULT_TIMEOUT) -> str:
        """导航到 URL"""
        self._page.goto(url, wait_until=wait_until, timeout=timeout)
        return self._page.url

    def click(self, selector: str, timeout: int = DEFAULT_TIMEOUT, button: str = "left",
              modifiers: List[str] = None, delay: int = 0, force: bool = False,
              continue_on_error: bool = False):
        """点击元素"""
        self._page.click(selector, timeout=timeout, button=button,
                         modifiers=modifiers or [], delay=delay, force=force)

    def dblclick(self, selector: str, timeout: int = DEFAULT_TIMEOUT, button: str = "left",
                 modifiers: List[str] = None, delay: int = 0):
        """双击元素"""
        self._page.dblclick(selector, timeout=timeout, button=button,
                            modifiers=modifiers or [], delay=delay)

    def type(self, selector: str, text: str, delay: int = 50, timeout: int = DEFAULT_TIMEOUT,
             clear: bool = True):
        """输入文本（先清空再输入）"""
        self._page.click(selector, timeout=timeout)
        if clear:
            self._page.keyboard.press("Control+a")
            self._page.keyboard.type(text, delay=delay)
        else:
            self._page.keyboard.type(text, delay=delay)

    def fill(self, selector: str, text: str, timeout: int = DEFAULT_TIMEOUT):
        """使用 Playwright fill（直接设置值+触发事件，适合 React）"""
        self._page.fill(selector, text, timeout=timeout)

    def click_ud(self, selector: str, timeout: int = DEFAULT_TIMEOUT):
        """支持 ud__ 前缀的选择器（class*=XXX 的简写）"""
        # selector 格式: "ud__dialog__root >> ud__dialog__content >> input"
        # 转换为: [class*=ud__dialog__root] [class*=ud__dialog__content] input
        converted = selector
        import re
        parts = converted.split(">>")
        css_parts = []
        for part in parts:
            part = part.strip()
            if "*=" not in part and "#" not in part and "." not in part:
                # 可能是 tag name
                if re.match(r'^[a-zA-Z]', part):
                    css_parts.append(part)
                else:
                    css_parts.append(part)
            else:
                css_parts.append(part)
        final_selector = " ".join(css_parts)
        self._page.click(final_selector, timeout=timeout)

    def press(self, key: str, selector: str = None, delay: int = 0):
        """按键"""
        if selector:
            self._page.click(selector)
        self._page.keyboard.press(key, delay=delay)

    def wait_for_selector(self, selector: str, timeout: int = DEFAULT_TIMEOUT,
                          state: str = "visible"):
        """等待元素出现"""
        self._page.wait_for_selector(selector, timeout=timeout, state=state)

    def wait_for_timeout(self, ms: int):
        """固定等待"""
        self._page.wait_for_timeout(ms)

    def extract(self, selector: str, attr: str = None, text: bool = True,
                all_: bool = False) -> Any:
        """
        提取内容
        attr=None + text=True  → 拿文本
        attr='href'            → 拿属性
        all_=True              → 返回列表
        """
        if all_:
            els = self._page.query_selector_all(selector)
            if attr:
                return [e.get_attribute(attr) for e in els]
            return [e.text_content() for e in els]
        else:
            el = self._page.query_selector(selector)
            if not el:
                return None
            if attr:
                return el.get_attribute(attr)
            return el.text_content()

    def extract_table(self, selector: str = "table") -> List[Dict[str, str]]:
        """提取表格数据（返回列表 of 字典）"""
        rows = self._page.query_selector_all(f"{selector} tr")
        headers = []
        data = []
        for i, row in enumerate(rows):
            cells = row.query_selector_all("th, td")
            cell_texts = [c.text_content().strip() for c in cells]
            if i == 0:
                headers = cell_texts
            else:
                data.append(dict(zip(headers, cell_texts)))
        return data

    def screenshot(self, path: str, full_page: bool = True,
                   selector: str = None, type_: str = "png") -> int:
        """截图，返回文件大小"""
        if selector:
            el = self._page.query_selector(selector)
            path2 = path
        else:
            el = None
            path2 = path

        if el:
            el.screenshot(path=path2)
        else:
            self._page.screenshot(path=path2, full_page=full_page, type=type_)
        return os.path.getsize(path)

    def scroll(self, selector: str = None, x: int = 0, y: int = None,
               to: str = "bottom", delta_y: int = 300):
        """
        滚动页面
        to='bottom' / 'top' → 滚动到顶/底部
        delta_y → 每次滚动像素（默认 300）
        """
        if selector:
            el = self._page.query_selector(selector)
            if el:
                el.scroll_into_view_if_needed()
            return

        if to == "bottom":
            self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        elif to == "top":
            self._page.evaluate("window.scrollTo(0, 0)")
        else:
            self._page.evaluate(f"window.scrollBy({x}, {y or delta_y})")

    def eval_js(self, script: str, args: List[Any] = None):
        """执行 JavaScript，返回结果。可选传入 args 列表作为 evaluate 的附加参数。"""
        if args:
            return self._page.evaluate(script, *args)
        return self._page.evaluate(script)

    def get_cookies(self) -> List[Dict[str, Any]]:
        return self._page.context.cookies()

    def set_cookies(self, cookies: List[Dict[str, Any]]):
        self._page.context.add_cookies(cookies)

    def html(self, selector: str = None) -> str:
        """获取页面 HTML"""
        if selector:
            el = self._page.query_selector(selector)
            return el.inner_html() if el else ""
        return self._page.content()

    def url(self) -> str:
        return self._page.url

    def title(self) -> str:
        return self._page.title()

    def close_page(self):
        if self._page:
            self._page.close()


# ──────────────────────────────────────────
# 动作序列执行器
# ──────────────────────────────────────────

def run_actions(actions: List[Dict[str, Any]], cdp_url: str = DEFAULT_CDP_URL) -> Dict[str, Any]:
    """
    执行动作序列，返回结果
    actions: [{"action": "nav", "url": "..."}, {"action": "click", "selector": "..."}, ...]
    """
    result = {"steps": [], "final_url": "", "title": "", "screenshots": [], "extracted": {}}

    with BrowserClient(cdp_url=cdp_url) as client:
        for i, step in enumerate(actions):
            action = step.get("action")
            step_as = step.get("as")  # 提取元数据，避免透传给 client
            continue_on_error = step.get("continue_on_error", False)
            args = {k: v for k, v in step.items()
                    if k not in ("action", "continue_on_error", "as")}

            try:
                if action == "nav":
                    url = client.nav(**args)
                    result["final_url"] = url
                    result["steps"].append({"action": action, "url": url, "ok": True})

                elif action == "click":
                    client.click(**args)
                    result["steps"].append({"action": action, "ok": True, **args})

                elif action == "dblclick":
                    client.dblclick(**args)
                    result["steps"].append({"action": action, "ok": True, **args})

                elif action == "type":
                    client.type(**args)
                    result["steps"].append({"action": action, "ok": True, **args})

                elif action == "fill":
                    client.fill(**args)
                    result["steps"].append({"action": action, "ok": True, **args})

                elif action == "click_ud":
                    client.click_ud(**args)
                    result["steps"].append({"action": action, "ok": True, **args})

                elif action == "press":
                    client.press(**args)
                    result["steps"].append({"action": action, "ok": True, **args})

                elif action == "wait_selector":
                    client.wait_for_selector(**args)
                    result["steps"].append({"action": action, "ok": True, **args})

                elif action == "wait_timeout":
                    client.wait_for_timeout(**args)
                    result["steps"].append({"action": action, "ok": True, **args})

                elif action == "extract":
                    val = client.extract(**args)
                    key = step_as or f"extract_{i}"
                    result["extracted"][key] = val
                    result["steps"].append({"action": action, "ok": True, "key": key, "value": str(val)[:100]})

                elif action == "extract_table":
                    val = client.extract_table(**args)
                    key = step_as or f"table_{i}"
                    result["extracted"][key] = val
                    result["steps"].append({"action": action, "ok": True, "key": key, "rows": len(val)})

                elif action == "screenshot":
                    size = client.screenshot(**args)
                    result["screenshots"].append(args.get("path", ""))
                    result["steps"].append({"action": action, "ok": True, "size": size, **args})

                elif action == "scroll":
                    client.scroll(**args)
                    result["steps"].append({"action": action, "ok": True, **args})

                elif action == "eval_js":
                    val = client.eval_js(**args)
                    result["steps"].append({"action": action, "ok": True, "value": str(val)[:200]})

            except Exception as e:
                result["steps"].append({"action": action, "ok": False, "error": str(e), **args})
                if not continue_on_error:
                    break

        result["title"] = client.title()

    return result


if __name__ == "__main__":
    # 快速测试
    import sys
    result = run_actions([
        {"action": "nav", "url": "https://www.baidu.com"},
        {"action": "screenshot", "path": "../screenshots/client_test.png", "full_page": True},
    ])
    print(json.dumps(result, ensure_ascii=False, indent=2))
