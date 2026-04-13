"""
Playwright CDP 客户端
- 连接到已有 Chrome（端口 9222）
- 所有交互操作通过这个 Client 进行
- 内置自动重连
"""
from playwright.sync_api import sync_playwright, Playwright
from typing import Optional, Dict, Any, List
import json, time, re, os, sys

# Windows GBK 兼容
if sys.stdout.encoding != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

DEFAULT_CDP_URL = "http://127.0.0.1:9222"
DEFAULT_TIMEOUT = 30000  # ms


class BrowserClient:
    """复用 Chrome 调试端口的 Playwright 客户端

    使用方式:
        with BrowserClient() as client:
            client.nav("https://example.com")
            client.click("#btn")
    """

    def __init__(self, cdp_url: str = DEFAULT_CDP_URL,
                 headless: bool = False,
                 max_retries: int = 3,
                 retry_delay: float = 1.5):
        self.cdp_url = cdp_url
        self.headless = headless
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._pw: Optional[Playwright] = None
        self._browser = None
        self._page = None

    # ─── 上下文管理器 ───
    def __enter__(self):
        self._pw = sync_playwright().start()
        self._connect_browser()
        return self

    def __exit__(self, *args):
        self._close()

    def _close(self):
        """安全关闭"""
        if self._page:
            try:
                self._page.close()
            except Exception:
                pass
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
        if self._pw:
            try:
                self._pw.stop()
            except Exception:
                pass
        self._pw = None
        self._browser = None
        self._page = None

    def _connect_browser(self):
        """连接浏览器，支持重试"""
        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                self._browser = self._pw.chromium.connect_over_cdp(self.cdp_url)
                contexts = self._browser.contexts
                if contexts and contexts[0].pages:
                    self._page = contexts[0].pages[0]
                else:
                    self._page = self._browser.new_page()
                return
            except Exception as e:
                last_err = e
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                continue
        raise RuntimeError(
            f"无法连接到 Chrome CDP ({self.cdp_url}): "
            f"{last_err}（已尝试 {self.max_retries} 次）"
        )

    def reconnect(self):
        """主动重连（浏览器断开后调用）"""
        self._close()
        self._pw = sync_playwright().start()
        self._connect_browser()

    @property
    def page(self):
        return self._page

    # ──────────────────────────────────────────
    # 基础信息
    # ──────────────────────────────────────────
    def url(self) -> str:
        return self._page.url if self._page else ""

    def title(self) -> str:
        return self._page.title() if self._page else ""

    def close_page(self):
        if self._page:
            try:
                self._page.close()
            except Exception:
                pass

    # ──────────────────────────────────────────
    # 导航
    # ──────────────────────────────────────────
    def nav(self, url: str, wait_until: str = "load",
            timeout: int = DEFAULT_TIMEOUT) -> str:
        """导航到 URL，返回最终 URL"""
        self._page.goto(url, wait_until=wait_until, timeout=timeout)
        return self._page.url

    # ──────────────────────────────────────────
    # 点击
    # ──────────────────────────────────────────
    def click(self, selector: str, timeout: int = DEFAULT_TIMEOUT,
              button: str = "left", modifiers: List[str] = None,
              delay: int = 0, force: bool = False,
              continue_on_error: bool = False):
        """点击元素，支持 ud__ / :text / :has-text 选择器"""
        css = self._convert_selector(selector)
        try:
            self._page.click(css, timeout=timeout, button=button,
                           modifiers=modifiers or [], delay=delay, force=force)
        except Exception as e:
            if continue_on_error:
                return  # 跳过
            raise

    def dblclick(self, selector: str, timeout: int = DEFAULT_TIMEOUT,
                 button: str = "left", modifiers: List[str] = None,
                 delay: int = 0):
        """双击"""
        css = self._convert_selector(selector)
        self._page.dblclick(css, timeout=timeout, button=button,
                          modifiers=modifiers or [], delay=delay)

    def rightclick(self, selector: str, timeout: int = DEFAULT_TIMEOUT):
        """右键菜单"""
        css = self._convert_selector(selector)
        self._page.click(css, timeout=timeout, button="right")

    def hover(self, selector: str, timeout: int = DEFAULT_TIMEOUT):
        """悬停"""
        css = self._convert_selector(selector)
        self._page.hover(css, timeout=timeout)

    def select(self, selector: str, value: str, timeout: int = DEFAULT_TIMEOUT):
        """下拉框选择"""
        css = self._convert_selector(selector)
        self._page.select_option(css, value, timeout=timeout)

    # ──────────────────────────────────────────
    # 输入
    # ──────────────────────────────────────────
    def type(self, selector: str, text: str, delay: int = 50,
             timeout: int = DEFAULT_TIMEOUT, clear: bool = True):
        """先清空再输入（适合标准 input）"""
        css = self._convert_selector(selector)
        self._page.click(css, timeout=timeout)
        if clear:
            # 全选再删除
            self._page.keyboard.press("Control+a")
            self._page.keyboard.press("Delete")
        self._page.keyboard.type(text, delay=delay)

    def fill(self, selector: str, text: str, timeout: int = DEFAULT_TIMEOUT):
        """直接设置值（适合 React/Vue 等框架的受控组件）"""
        css = self._convert_selector(selector)
        self._page.fill(css, text, timeout=timeout)

    def press(self, key: str, selector: str = None, delay: int = 0):
        """按键（可选：先聚焦到某元素）"""
        if selector:
            css = self._convert_selector(selector)
            self._page.click(css, timeout=DEFAULT_TIMEOUT)
        self._page.keyboard.press(key, delay=delay)

    def hotkey(self, *keys):
        """组合键，如 hotkey("Control", "a")"""
        self._page.keyboard.press("+".join(keys))

    # ──────────────────────────────────────────
    # 等待
    # ──────────────────────────────────────────
    def wait_for_selector(self, selector: str, timeout: int = DEFAULT_TIMEOUT,
                          state: str = "visible"):
        """等待元素出现/消失"""
        css = self._convert_selector(selector)
        self._page.wait_for_selector(css, timeout=timeout, state=state)

    def wait_for_timeout(self, ms: int):
        """固定等待"""
        self._page.wait_for_timeout(ms)

    def wait_for_url(self, pattern: str, timeout: int = DEFAULT_TIMEOUT):
        """等待 URL 匹配"""
        self._page.wait_for_url(pattern, timeout=timeout)

    # ──────────────────────────────────────────
    # 提取
    # ──────────────────────────────────────────
    def extract(self, selector: str, attr: str = None,
                text: bool = True, all_: bool = False) -> Any:
        """提取内容

        attr=None + text=True  → 拿文本
        attr='href'            → 拿属性
        all_=True              → 返回列表
        """
        css = self._convert_selector(selector)
        if all_:
            els = self._page.query_selector_all(css)
            if not els:
                return []
            if attr:
                return [e.get_attribute(attr) for e in els]
            return [e.text_content() for e in els]
        else:
            el = self._page.query_selector(css)
            if not el:
                return None
            if attr:
                return el.get_attribute(attr)
            return el.text_content()

    def extract_table(self, selector: str = "table") -> List[Dict[str, str]]:
        """提取表格，返回 [{col1: val1, col2: val2}, ...]"""
        css = self._convert_selector(selector)
        rows = self._page.query_selector_all(f"{css} tr")
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

    def extract_all(self, selector: str, schema: Dict[str, str] = None
                   ) -> List[Dict[str, Any]]:
        """
        批量提取多条记录

        schema: {"name": "div.title", "href": "a@href", "price": ".price"}
               → "div.title" = 文本，"a@href" = 属性
        """
        results = []
        els = self._page.query_selector_all(selector)
        for el in els:
            record = {}
            if schema:
                for key, sel in schema.items():
                    if "@" in sel:
                        tag_sel, attr = sel.split("@", 1)
                        tag_el = el.query_selector(tag_sel)
                        record[key] = tag_el.get_attribute(attr) if tag_el else None
                    else:
                        tag_el = el.query_selector(sel)
                        record[key] = tag_el.text_content().strip() if tag_el else None
            results.append(record)
        return results

    # ──────────────────────────────────────────
    # 截图
    # ──────────────────────────────────────────
    def screenshot(self, path: str, full_page: bool = True,
                   selector: str = None, type_: str = "png") -> int:
        """截图，返回文件大小（字节）"""
        if selector:
            css = self._convert_selector(selector)
            el = self._page.query_selector(css)
        else:
            el = None

        os.makedirs(os.path.dirname(path), exist_ok=True)
        if el:
            el.screenshot(path=path)
        else:
            self._page.screenshot(path=path, full_page=full_page, type=type_)

        try:
            return os.path.getsize(path)
        except Exception:
            return 0

    # ──────────────────────────────────────────
    # 滚动
    # ──────────────────────────────────────────
    def scroll(self, selector: str = None, x: int = 0, y: int = None,
               to: str = "bottom", delta_y: int = 500):
        """滚动页面"""
        if selector:
            css = self._convert_selector(selector)
            el = self._page.query_selector(css)
            if el:
                el.scroll_into_view_if_needed()
            return

        if to == "bottom":
            self._page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight)")
        elif to == "top":
            self._page.evaluate("window.scrollTo(0, 0)")
        elif to == "middle":
            self._page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight / 2)")
        else:
            self._page.evaluate(f"window.scrollBy({x}, {y or delta_y})")

    def scroll_until_load(self, selector: str, delta_y: int = 500,
                          max_scrolls: int = 20):
        """滚动直到新元素出现（懒加载翻页）"""
        last_count = 0
        for _ in range(max_scrolls):
            els = self._page.query_selector_all(selector)
            current_count = len(els)
            if current_count > last_count:
                last_count = current_count
                self._page.evaluate(f"window.scrollBy(0, {delta_y})")
                self.wait_for_timeout(300)
            else:
                break

    # ──────────────────────────────────────────
    # JS / Cookies / HTML
    # ──────────────────────────────────────────
    def eval_js(self, script: str, *args) -> Any:
        """执行 JavaScript，可传入 args 作为 $0, $1 ..."""
        if args:
            return self._page.evaluate(script, *args)
        return self._page.evaluate(script)

    def get_cookies(self) -> List[Dict[str, Any]]:
        return self._page.context.cookies()

    def set_cookies(self, cookies: List[Dict[str, Any]]):
        self._page.context.add_cookies(cookies)

    def html(self, selector: str = None) -> str:
        """获取页面/元素 HTML"""
        if selector:
            css = self._convert_selector(selector)
            el = self._page.query_selector(css)
            return el.inner_html() if el else ""
        return self._page.content()

    # ──────────────────────────────────────────
    # 选择器转换
    # ──────────────────────────────────────────
    UD_RE = re.compile(r'ud__([a-zA-Z0-9_-]+)')

    def _convert_selector(self, selector: str) -> str:
        """
        支持多种简写语法的选择器转换

        1. ud__ 前缀（class*=XXX 的简写）
           "ud__dialog__root >> ud__dialog__content >> input"
             → "[class*=ud__dialog__root] [class*=ud__dialog__content] input"

        2. :text() / :has-text() / :near() （Playwright 内置）
           "button:text('登录')" → 保持原样（Playwright 原生支持）

        3. >> 链接（多个选择器组合）
        """
        if not selector or "ud__" not in selector:
            return selector

        # 处理 ud__ 前缀
        def replace_ud(match):
            class_name = match.group(1)
            # 还原为连字符格式（ud__dialog_root → dialog-root）
            hyphened = class_name.replace("_", "-")
            return f"[class*={hyphened}]"

        converted = self.UD_RE.sub(replace_ud, selector)
        return converted


# ──────────────────────────────────────────
# 动作序列执行器
# ──────────────────────────────────────────

def run_actions(actions: List[Dict[str, Any]],
                cdp_url: str = DEFAULT_CDP_URL,
                reconnect_on_error: bool = True,
                max_retries: int = 2) -> Dict[str, Any]:
    """
    执行动作序列，返回结果

    支持的动作: nav / click / dblclick / rightclick / hover /
                type / fill / press / hotkey /
                wait_selector / wait_timeout / wait_url /
                extract / extract_all / extract_table /
                screenshot / scroll / scroll_until_load /
                eval_js / get_cookies / set_cookies / html
    """
    result = {
        "steps": [],
        "final_url": "",
        "title": "",
        "screenshots": [],
        "extracted": {},
        "ok": True
    }

    with BrowserClient(cdp_url=cdp_url) as client:
        for i, step in enumerate(actions):
            action = step.get("action")
            as_key = step.get("as")
            continue_on_error = step.get("continue_on_error", False)
            # 提取动作参数（排除元数据字段）
            args = {k: v for k, v in step.items()
                    if k not in ("action", "continue_on_error", "as")}

            step_result = {"action": action, "ok": False, **args}

            try:
                # ── 导航 ──
                if action == "nav":
                    url = client.nav(**args)
                    result["final_url"] = url
                    step_result.update({"ok": True, "url": url})

                # ── 点击 ──
                elif action == "click":
                    client.click(**args)
                    step_result["ok"] = True

                elif action == "dblclick":
                    client.dblclick(**args)
                    step_result["ok"] = True

                elif action == "rightclick":
                    client.rightclick(**args)
                    step_result["ok"] = True

                elif action == "hover":
                    client.hover(**args)
                    step_result["ok"] = True

                # ── 输入 ──
                elif action == "type":
                    client.type(**args)
                    step_result["ok"] = True

                elif action == "fill":
                    client.fill(**args)
                    step_result["ok"] = True

                elif action == "press":
                    client.press(**args)
                    step_result["ok"] = True

                elif action == "hotkey":
                    client.hotkey(*step.get("keys", []))
                    step_result["ok"] = True

                # ── 等待 ──
                elif action == "wait_selector":
                    client.wait_for_selector(**args)
                    step_result["ok"] = True

                elif action == "wait_timeout":
                    client.wait_for_timeout(**args)
                    step_result["ok"] = True

                elif action == "wait_url":
                    client.wait_for_url(**args)
                    step_result["ok"] = True

                # ── 提取 ──
                elif action == "extract":
                    val = client.extract(**args)
                    key = as_key or f"v{i}"
                    result["extracted"][key] = val
                    step_result.update({"ok": True, "key": key,
                                       "preview": str(val)[:80] if val else ""})

                elif action == "extract_all":
                    val = client.extract_all(**args)
                    key = as_key or f"list{i}"
                    result["extracted"][key] = val
                    step_result.update({"ok": True, "key": key, "count": len(val)})

                elif action == "extract_table":
                    val = client.extract_table(**args)
                    key = as_key or f"table{i}"
                    result["extracted"][key] = val
                    step_result.update({"ok": True, "key": key, "rows": len(val)})

                # ── 截图 ──
                elif action == "screenshot":
                    size = client.screenshot(**args)
                    result["screenshots"].append(args.get("path", ""))
                    step_result.update({"ok": True, "size": size})

                # ── 滚动 ──
                elif action == "scroll":
                    client.scroll(**args)
                    step_result["ok"] = True

                elif action == "scroll_until_load":
                    client.scroll_until_load(**args)
                    step_result["ok"] = True

                # ── JS ──
                elif action == "eval_js":
                    val = client.eval_js(**args)
                    step_result.update({"ok": True, "result": str(val)[:100]})

                elif action == "get_cookies":
                    val = client.get_cookies()
                    result["extracted"]["cookies"] = val
                    step_result.update({"ok": True, "count": len(val)})

                elif action == "set_cookies":
                    client.set_cookies(**args)
                    step_result["ok"] = True

                elif action == "html":
                    val = client.html(**args)
                    key = as_key or f"html{i}"
                    result["extracted"][key] = val
                    step_result.update({"ok": True, "key": key,
                                       "size": len(val) if val else 0})

                else:
                    step_result["ok"] = False
                    step_result["error"] = f"Unknown action: {action}"

            except Exception as e:
                step_result["ok"] = False
                step_result["error"] = str(e)[:120]
                step_result["error_type"] = _classify_error(e)
                # 自动重连
                if reconnect_on_error and "disconnect" in str(e).lower():
                    try:
                        client.reconnect()
                        step_result["reconnected"] = True
                    except Exception:
                        pass
                if not continue_on_error:
                    result["ok"] = False
                    result["steps"].append(step_result)
                    break

            result["steps"].append(step_result)

        result["title"] = client.title()
        result["final_url"] = client.url()

    return result


def _classify_error(exception: Exception) -> str:
    """错误类型分类"""
    msg = str(exception).lower()
    name = type(exception).__name__
    if "selector" in msg or "not found" in name.lower():
        return "SELECTOR_NOT_FOUND"
    elif "timeout" in msg or "timed out" in name.lower():
        return "TIMEOUT"
    elif "disconnect" in msg or "close" in msg:
        return "BROWSER_DISCONNECTED"
    elif "net::" in msg:
        return "NETWORK_ERROR"
    return "UNKNOWN"


if __name__ == "__main__":
    result = run_actions([
        {"action": "nav", "url": "https://www.baidu.com"},
        {"action": "wait_timeout", "ms": 1000},
        {"action": "screenshot",
         "path": str(Path(__file__).parent.parent / "screenshots" / "client_test.png"),
         "full_page": True},
    ])
    print(json.dumps(result, ensure_ascii=False, indent=2))
