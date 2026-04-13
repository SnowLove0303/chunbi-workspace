"""
高级操作 - 常用交互模式封装
每个操作都是原子的，可独立调用
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

# 原子操作列表
ATOMIC_ACTIONS = [
    "nav", "click", "dblclick", "type", "press",
    "wait_selector", "wait_timeout", "extract", "extract_table",
    "screenshot", "scroll", "eval_js", "get_cookies", "set_cookies", "html"
]


# ──────────────────────────────────────────
# 常用操作工厂
# ──────────────────────────────────────────

def nav(url: str, wait_until: str = "load", timeout: int = 30000) -> Dict[str, Any]:
    return {"action": "nav", "url": url, "wait_until": wait_until, "timeout": timeout}


def click(selector: str, timeout: int = 30000, button: str = "left",
          delay: int = 0, force: bool = False, continue_on_error: bool = False) -> Dict[str, Any]:
    return {"action": "click", "selector": selector, "timeout": timeout,
            "button": button, "delay": delay, "force": force,
            "continue_on_error": continue_on_error}


def type_text(selector: str, text: str, delay: int = 50,
              timeout: int = 30000, clear: bool = True) -> Dict[str, Any]:
    return {"action": "type", "selector": selector, "text": text,
            "delay": delay, "timeout": timeout, "clear": clear}


def press_key(key: str, selector: str = None, delay: int = 0) -> Dict[str, Any]:
    return {"action": "press", "key": key, "selector": selector, "delay": delay}


def wait(selector: str, timeout: int = 30000, state: str = "visible") -> Dict[str, Any]:
    return {"action": "wait_selector", "selector": selector, "timeout": timeout, "state": state}


def wait_ms(ms: int) -> Dict[str, Any]:
    return {"action": "wait_timeout", "ms": ms}


def extract_text(selector: str, attr: str = None, all_: bool = False, as_: str = None) -> Dict[str, Any]:
    d = {"action": "extract", "selector": selector, "text": True, "all_": all_}
    if attr:
        d["attr"] = attr
    if as_:
        d["as"] = as_
    return d


def extract_table(selector: str = "table", as_: str = None) -> Dict[str, Any]:
    d = {"action": "extract_table", "selector": selector}
    if as_:
        d["as"] = as_
    return d


def screenshot(path: str, full_page: bool = True, selector: str = None) -> Dict[str, Any]:
    d = {"action": "screenshot", "path": path, "full_page": full_page}
    if selector:
        d["selector"] = selector
    return d


def scroll_to(to: str = "bottom", selector: str = None, delta_y: int = 300) -> Dict[str, Any]:
    return {"action": "scroll", "to": to, "selector": selector, "delta_y": delta_y}


def evaljs(script: str) -> Dict[str, Any]:
    return {"action": "eval_js", "script": script}


# ──────────────────────────────────────────
# 场景模板
# ──────────────────────────────────────────

def login_template(username_selector: str, password_selector: str,
                   username: str, password: str, submit_selector: str,
                   after_login_wait: str = None) -> List[Dict[str, Any]]:
    """标准登录流程"""
    steps = [
        type_text(username_selector, username),
        type_text(password_selector, password),
        click(submit_selector, delay=300),
    ]
    if after_login_wait:
        steps.append(wait(after_login_wait))
    return steps


def table_extract_template(table_selector: str = "table", page_anchor: str = None,
                          max_pages: int = 10) -> List[Dict[str, Any]]:
    """翻页提取表格数据"""
    steps = [
        wait(table_selector, state="visible"),
        extract_table(selector=table_selector, as_="page_data"),
    ]
    if page_anchor:
        # 尝试翻页（通用逻辑：找"下一页"按钮并点击）
        steps.extend([
            scroll_to("bottom"),
            wait_ms(500),
            # 通用下一页逻辑（需要根据实际页面调整）
        ])
    return steps


def form_submit_template(form_url: str, fields: Dict[str, str],
                        submit_selector: str, after_submit_selector: str,
                        result_selector: str = None) -> List[Dict[str, Any]]:
    """表单提交流程"""
    steps = [nav(form_url)]
    for sel, val in fields.items():
        steps.append(type_text(sel, val))
    steps.append(click(submit_selector, delay=500))
    if after_submit_selector:
        steps.append(wait(after_submit_selector, timeout=10000))
    if result_selector:
        steps.append(extract_text(result_selector, as_="result"))
    return steps


# ──────────────────────────────────────────
# Workflow JSON 转动作序列
# ──────────────────────────────────────────

def load_workflow_json(path: str) -> List[Dict[str, Any]]:
    """从 JSON 文件加载动作序列"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "steps" in data:
        return data["steps"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unknown workflow JSON format in {path}")


def save_workflow_json(path: str, workflow: List[Dict[str, Any]]):
    """保存动作序列到 JSON"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"steps": workflow}, f, ensure_ascii=False, indent=2)
