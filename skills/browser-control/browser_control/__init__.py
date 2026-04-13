# browser-control - 交互式浏览器自动化
from .client import BrowserClient, run_actions, DEFAULT_CDP_URL
from .actions import (
    nav, click, type_text, press_key, wait, wait_ms,
    extract_text, extract_table, screenshot, scroll_to, evaljs,
    login_template, form_submit_template, table_extract_template,
    load_workflow_json, save_workflow_json
)
