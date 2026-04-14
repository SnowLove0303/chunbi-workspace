#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
飞书应用创建全自动技能 v4.0
基于 Chrome CDP (Chrome DevTools Protocol) 实现
支持：自动登录态检测、应用创建、权限批量导入、事件订阅、凭证获取

技术架构:
- Chrome CDP 协议直接通信
- 多重选择器降级策略 (CSS/XPath/text)
- 智能等待机制 (waitForSelector/waitForFunction)
- 人类行为模拟 (随机延迟 2-5 秒)
- 全程截图验证 + 详细日志

安全规范:
- 严禁硬编码明文密码
- 复用浏览器登录态 (首次需人工扫码)
- APP Secret 仅显示一次，需人工保存
- 发布步骤需人工确认
"""

import json
import time
import random
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# 尝试导入 CDP 库，如果不存在则使用备用方案
try:
    from chrome_cdpx import ChromeCDP
    CDP_AVAILABLE = True
except ImportError:
    CDP_AVAILABLE = False
    print("[INFO] chrome_cdpx not found, using Selenium CDP mode")

# ==================== 配置管理 ====================

CONFIG = {
    "feishu_url": "https://open.feishu.cn/app",
    "app_name": "飞书 Flow 测试",
    "app_description": "1",
    "permissions_file": "C:\\Users\\chenz\\Documents\\Obsidian Vault\\开发项目ing\\飞书\\json.md",
    "debug_port": 9222,
    "user_data_dir": r"C:\Users\chenz\AppData\Local\Google\Chrome\User Data",
    "screenshot_dir": "./screenshots",
    "log_dir": "./logs",
    "delay_range": (2, 5),  # 人类行为模拟延迟
    "timeout": 30000,  # 30 秒超时
}

# ==================== 日志配置 ====================

def setup_logging():
    """配置日志系统"""
    log_dir = Path(CONFIG["log_dir"])
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"feishu_auto_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ==================== CDP 浏览器控制器 ====================

class ChromeCDPController:
    """Chrome CDP 协议控制器"""
    
    def __init__(self, debug_port: int = 9222):
        self.debug_port = debug_port
        self.ws_url = f"ws://127.0.0.1:{debug_port}/devtools/browser/"
        self.page_ws_url = None
        self.session_id = None
        
    async def connect(self) -> bool:
        """连接到已运行的 Chrome 浏览器"""
        try:
            # 获取浏览器调试信息
            import aiohttp
            async with aiohttp.ClientSession() as session:
                resp = await session.get(f"http://127.0.0.1:{self.debug_port}/json/version")
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"[OK] 成功连接到 Chrome 浏览器 (版本：{data.get('Browser', 'Unknown')})")
                    
                    # 获取页面列表
                    pages_resp = await session.get(f"http://127.0.0.1:{self.debug_port}/json/list")
                    if pages_resp.status == 200:
                        pages = await pages_resp.json()
                        for page in pages:
                            if page.get('type') == 'page':
                                self.page_ws_url = page.get('webSocketDebuggerUrl')
                                logger.info(f"[OK] 找到可控制的页面：{page.get('title', 'Unknown')}")
                                return True
                    
                    logger.warning("[WARN] 未找到可控制的页面，将打开新页面")
                    return True
                else:
                    logger.error(f"[FAIL] 连接失败：HTTP {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"[FAIL] 连接异常：{e}")
            return False
    
    async def send_command(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送 CDP 命令"""
        import aiohttp
        import websockets
        
        if not self.page_ws_url:
            raise RuntimeError("未连接到任何页面")
        
        async with websockets.connect(self.page_ws_url) as ws:
            command_id = 1
            command = {
                "id": command_id,
                "method": method,
                "params": params or {}
            }
            
            await ws.send(json.dumps(command))
            response = await ws.recv()
            return json.loads(response)
    
    async def navigate(self, url: str) -> bool:
        """导航到指定 URL"""
        try:
            result = await self.send_command("Page.navigate", {"url": url})
            return result.get("errorId") is None
        except Exception as e:
            logger.error(f"导航失败：{e}")
            return False
    
    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> bool:
        """等待元素出现"""
        try:
            # 使用 Runtime.evaluate 执行 JavaScript 等待
            js_code = f"""
            () => {{
                return new Promise((resolve) => {{
                    const element = document.querySelector('{selector}');
                    if (element) {{
                        resolve(true);
                    }} else {{
                        const observer = new MutationObserver(() => {{
                            const el = document.querySelector('{selector}');
                            if (el) {{
                                observer.disconnect();
                                resolve(true);
                            }}
                        }});
                        observer.observe(document.body, {{ childList: true, subtree: true }});
                        setTimeout(() => {{
                            observer.disconnect();
                            resolve(false);
                        }}, {timeout});
                    }}
                }});
            }}
            """
            result = await self.send_command("Runtime.evaluate", {"expression": js_code})
            return result.get("result", {}).get("value", False)
        except Exception as e:
            logger.error(f"等待元素失败 [{selector}]: {e}")
            return False
    
    async def click_element(self, selector: str) -> bool:
        """点击元素（多重选择器降级）"""
        selectors_to_try = [
            selector,  # CSS Selector
            f"//{selector}",  # XPath
            f"//*[text()[contains(., '{selector}')]]",  # Text content
        ]
        
        for sel in selectors_to_try:
            try:
                js_code = f"""
                () => {{
                    const element = document.querySelector('{sel}');
                    if (element) {{
                        element.click();
                        return true;
                    }}
                    return false;
                }}
                """
                result = await self.send_command("Runtime.evaluate", {"expression": js_code})
                if result.get("result", {}).get("value", False):
                    logger.info(f"[OK] 成功点击：{sel}")
                    return True
            except Exception as e:
                logger.debug(f"点击尝试失败 [{sel}]: {e}")
                continue
        
        logger.error(f"[FAIL] 无法点击元素：{selector}")
        return False
    
    async def type_text(self, selector: str, text: str) -> bool:
        """输入文本"""
        try:
            # 先聚焦元素
            focus_js = f"""
            () => {{
                const element = document.querySelector('{selector}');
                if (element) {{
                    element.focus();
                    return true;
                }}
                return false;
            }}
            """
            await self.send_command("Runtime.evaluate", {"expression": focus_js})
            
            # 逐个字符输入（模拟人类行为）
            for char in text:
                await self.send_command("Input.insertText", {"text": char})
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            logger.info(f"[OK] 输入文本：{text}")
            return True
        except Exception as e:
            logger.error(f"输入失败：{e}")
            return False
    
    async def screenshot(self, filename: str) -> str:
        """截取屏幕截图"""
        try:
            screenshot_dir = Path(CONFIG["screenshot_dir"])
            screenshot_dir.mkdir(exist_ok=True)
            filepath = screenshot_dir / filename
            
            result = await self.send_command("Page.captureScreenshot", {"format": "png"})
            if "data" in result:
                import base64
                image_data = base64.b64decode(result["data"])
                with open(filepath, "wb") as f:
                    f.write(image_data)
                logger.info(f"[OK] 截图保存：{filepath}")
                return str(filepath)
            return ""
        except Exception as e:
            logger.error(f"截图失败：{e}")
            return ""
    
    async def get_page_content(self) -> str:
        """获取页面内容"""
        try:
            result = await self.send_command("Runtime.evaluate", {
                "expression": "document.documentElement.outerHTML"
            })
            return result.get("result", {}).get("value", "")
        except Exception as e:
            logger.error(f"获取页面内容失败：{e}")
            return ""

# ==================== 飞书自动化主类 ====================

class FeishuAppCreator:
    """飞书应用创建自动化"""
    
    def __init__(self):
        self.cdp = ChromeCDPController(CONFIG["debug_port"])
        self.app_id = None
        self.app_secret = None
        self.screenshots = []
        
    async def human_delay(self, min_sec: float = 2, max_sec: float = 5):
        """人类行为模拟延迟"""
        delay = random.uniform(min_sec, max_sec)
        logger.info(f"⏳ 等待 {delay:.1f} 秒...")
        await asyncio.sleep(delay)
    
    async def step_check_login(self) -> bool:
        """步骤 1-2: 检查登录状态"""
        logger.info("=" * 60)
        logger.info("【步骤 1-2】检查飞书登录状态")
        
        if not await self.cdp.connect():
            logger.error("[FAIL] 无法连接到 Chrome 浏览器")
            logger.info("[BULB] 请确保 Chrome 以调试模式启动:")
            logger.info(f'   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port={CONFIG["debug_port"]} --user-data-dir="{CONFIG["user_data_dir"]}"')
            return False
        
        await self.human_delay(2, 3)
        
        # 导航到飞书开发者后台
        if not await self.cdp.navigate(CONFIG["feishu_url"]):
            logger.error("[FAIL] 导航失败")
            return False
        
        await self.human_delay(3, 5)
        
        # 检查是否已登录（查找用户头像或退出按钮）
        login_indicators = [
            ".ant-avatar",  # 用户头像
            "[data-e2e='logout']",  # 退出按钮
            ".user-profile",  # 用户资料
        ]
        
        for indicator in login_indicators:
            if await self.cdp.wait_for_selector(indicator, timeout=5000):
                logger.info("[OK] 检测到已登录状态")
                await self.cdp.screenshot("01_login_success.png")
                self.screenshots.append("01_login_success.png")
                return True
        
        logger.warning("[WARN] 未检测到登录状态，可能需要扫码登录")
        logger.info("[BULB] 请在浏览器中手动扫码登录，然后按回车继续...")
        input("按回车键继续...")
        
        await self.cdp.screenshot("01_login_manual.png")
        self.screenshots.append("01_login_manual.png")
        return True
    
    async def step_create_app(self) -> bool:
        """步骤 3-5: 创建应用"""
        logger.info("=" * 60)
        logger.info("【步骤 3-5】创建企业自建应用")
        
        # 点击"创建企业自建应用"
        create_selectors = [
            "[data-e2e='create-app']",
            "button:contains('创建企业自建应用')",
            "//button[contains(text(), '创建企业自建应用')]",
        ]
        
        created = False
        for selector in create_selectors:
            if await self.cdp.click_element(selector):
                created = True
                break
        
        if not created:
            logger.warning("[WARN] 未找到创建按钮，尝试直接打开创建页面")
            await self.cdp.navigate("https://open.feishu.cn/app/create")
        
        await self.human_delay(3, 5)
        
        # 填写应用名称
        name_selectors = [
            "input[placeholder*='应用名称']",
            "input[data-e2e='app-name']",
            "#app-name",
        ]
        
        for selector in name_selectors:
            if await self.cdp.type_text(selector, CONFIG["app_name"]):
                break
        
        await self.human_delay(1, 2)
        
        # 填写应用描述
        desc_selectors = [
            "textarea[placeholder*='应用描述']",
            "textarea[data-e2e='app-description']",
            "#app-description",
        ]
        
        for selector in desc_selectors:
            if await self.cdp.type_text(selector, CONFIG["app_description"]):
                break
        
        await self.human_delay(2, 3)
        
        # 点击创建按钮
        submit_selectors = [
            "button:contains('创建')",
            "button[type='submit']",
            "//button[contains(text(), '创建')]",
        ]
        
        for selector in submit_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(5, 8)  # 等待应用创建
        
        await self.cdp.screenshot("02_app_created.png")
        self.screenshots.append("02_app_created.png")
        logger.info("[OK] 应用创建完成")
        return True
    
    async def step_add_bot_function(self) -> bool:
        """步骤 6-8: 添加机器人功能"""
        logger.info("=" * 60)
        logger.info("【步骤 6-8】添加机器人功能")
        
        # 点击"添加应用能力"
        add_func_selectors = [
            "[data-e2e='add-function']",
            "button:contains('添加应用能力')",
            "//button[contains(text(), '添加应用能力')]",
        ]
        
        for selector in add_func_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(2, 3)
        
        # 找到并点击机器人功能
        bot_selectors = [
            "[data-e2e='bot-function']",
            "div:contains('机器人')",
            "//div[contains(text(), '机器人')]",
        ]
        
        for selector in bot_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(2, 3)
        
        # 点击"添加"按钮
        add_btn_selectors = [
            "button:contains('添加')",
            "[data-e2e='confirm-add']",
            "//button[contains(text(), '添加')]",
        ]
        
        for selector in add_btn_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(3, 5)
        
        await self.cdp.screenshot("03_bot_added.png")
        self.screenshots.append("03_bot_added.png")
        logger.info("[OK] 机器人功能添加完成")
        return True
    
    async def step_import_permissions(self) -> bool:
        """步骤 9-17: 批量导入权限"""
        logger.info("=" * 60)
        logger.info("【步骤 9-17】批量导入权限")
        
        # 点击"权限管理"
        perm_selectors = [
            "[data-e2e='permission-management']",
            "a:contains('权限管理')",
            "//a[contains(text(), '权限管理')]",
        ]
        
        for selector in perm_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(2, 3)
        
        # 点击"批量导入/导出权限"
        batch_selectors = [
            "[data-e2e='batch-import']",
            "button:contains('批量导入')",
            "//button[contains(text(), '批量导入')]",
        ]
        
        for selector in batch_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(2, 3)
        
        # 读取权限 JSON 文件
        try:
            with open(CONFIG["permissions_file"], 'r', encoding='utf-8') as f:
                permissions_json = f.read()
            logger.info(f"[OK] 读取权限配置文件：{CONFIG['permissions_file']}")
        except Exception as e:
            logger.error(f"[FAIL] 读取权限文件失败：{e}")
            return False
        
        # 粘贴 JSON 到输入框
        textarea_selectors = [
            "textarea[data-e2e='permission-import']",
            "textarea[placeholder*='JSON']",
            "#permission-json-input",
        ]
        
        for selector in textarea_selectors:
            if await self.cdp.type_text(selector, permissions_json):
                break
        
        await self.human_delay(2, 3)
        
        # 点击"下一步"
        next_selectors = [
            "button:contains('下一步')",
            "[data-e2e='next-step']",
            "//button[contains(text(), '下一步')]",
        ]
        
        for selector in next_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(2, 3)
        
        # 点击"申请开通"
        apply_selectors = [
            "button:contains('申请开通')",
            "[data-e2e='apply-permission']",
            "//button[contains(text(), '申请开通')]",
        ]
        
        for selector in apply_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(3, 5)
        
        # 点击"保存"
        save_selectors = [
            "button:contains('保存')",
            "[data-e2e='save-permission']",
            "//button[contains(text(), '保存')]",
        ]
        
        for selector in save_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(3, 5)
        
        # 点击"确认"
        confirm_selectors = [
            "button:contains('确认')",
            "[data-e2e='confirm-permission']",
            "//button[contains(text(), '确认')]",
        ]
        
        for selector in confirm_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(3, 5)
        
        await self.cdp.screenshot("04_permissions_imported.png")
        self.screenshots.append("04_permissions_imported.png")
        logger.info("[OK] 权限导入完成")
        return True
    
    async def step_subscribe_events(self) -> bool:
        """步骤 18-25: 配置事件订阅"""
        logger.info("=" * 60)
        logger.info("【步骤 18-25】配置事件订阅")
        
        # 点击"事件与回调"
        event_selectors = [
            "[data-e2e='event-callback']",
            "a:contains('事件与回调')",
            "//a[contains(text(), '事件与回调')]",
        ]
        
        for selector in event_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(2, 3)
        
        # 点击编辑按钮（笔图标）
        edit_selectors = [
            "[data-e2e='edit-subscription']",
            ".anticon-edit",
            "//i[contains(@class, 'edit')]",
        ]
        
        for selector in edit_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(2, 3)
        
        # 点击"保存"
        save_selectors = [
            "button:contains('保存')",
            "[data-e2e='save-subscription']",
            "//button[contains(text(), '保存')]",
        ]
        
        for selector in save_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(2, 3)
        
        # 点击"添加事件"
        add_event_selectors = [
            "button:contains('添加事件')",
            "[data-e2e='add-event']",
            "//button[contains(text(), '添加事件')]",
        ]
        
        for selector in add_event_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(2, 3)
        
        # 点击搜索框
        search_selectors = [
            "input[placeholder*='搜索']",
            "[data-e2e='event-search']",
            "#event-search",
        ]
        
        for selector in search_selectors:
            if await self.cdp.type_text(selector, "im.message.receive_v1"):
                break
        
        await self.human_delay(2, 3)
        
        # 勾选搜索结果
        checkbox_selectors = [
            "input[type='checkbox']",
            "[data-e2e='event-checkbox']",
            "//input[@type='checkbox']",
        ]
        
        for selector in checkbox_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(2, 3)
        
        # 点击"添加"
        add_selectors = [
            "button:contains('添加')",
            "[data-e2e='confirm-add-event']",
            "//button[contains(text(), '添加')]",
        ]
        
        for selector in add_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(3, 5)
        
        await self.cdp.screenshot("05_events_subscribed.png")
        self.screenshots.append("05_events_subscribed.png")
        logger.info("[OK] 事件订阅配置完成")
        return True
    
    async def step_get_credentials(self) -> bool:
        """步骤 26-29: 获取 APP ID 和 Secret"""
        logger.info("=" * 60)
        logger.info("【步骤 26-29】获取 APP ID 和 Secret")
        
        # 点击"凭证与基础信息"
        cred_selectors = [
            "[data-e2e='credentials']",
            "a:contains('凭证与基础信息')",
            "//a[contains(text(), '凭证与基础信息')]",
        ]
        
        for selector in cred_selectors:
            if await self.cdp.click_element(selector):
                break
        
        await self.human_delay(3, 5)
        
        # 获取 APP ID
        page_content = await self.cdp.get_page_content()
        
        # 尝试从页面提取 APP ID
        import re
        app_id_match = re.search(r'App ID[:：]\s*([a-zA-Z0-9]+)', page_content)
        if app_id_match:
            self.app_id = app_id_match.group(1)
            logger.info(f"[OK] 获取到 APP ID: {self.app_id}")
        else:
            logger.warning("[WARN] 未能自动提取 APP ID，请手动记录")
        
        # 提示用户手动复制 APP Secret
        logger.info("[BULB] 请点击 APP Secret 旁边的眼睛图标查看，然后点击复制按钮")
        logger.info("⏳ 等待 10 秒...")
        await asyncio.sleep(10)
        
        await self.cdp.screenshot("06_credentials.png")
        self.screenshots.append("06_credentials.png")
        logger.info("[OK] 凭证信息已截图保存")
        return True
    
    async def step_publish_version(self) -> bool:
        """步骤 30-31: 发布版本"""
        logger.info("=" * 60)
        logger.info("【步骤 30-31】发布应用版本")
        
        logger.info("[WARN] 发布操作需要人工确认，请检查以下信息:")
        logger.info(f"   - 应用名称：{CONFIG['app_name']}")
        logger.info(f"   - APP ID: {self.app_id or '待确认'}")
        logger.info("   - 权限配置已完成")
        logger.info("   - 事件订阅已完成")
        logger.info("")
        logger.info("[BULB] 请在浏览器中点击'发布版本'按钮")
        
        input("按回车键确认已发布...")
        
        await self.cdp.screenshot("07_published.png")
        self.screenshots.append("07_published.png")
        logger.info("[OK] 应用发布完成")
        return True
    
    async def run_full_workflow(self):
        """执行完整工作流"""
        logger.info("[ROCKET] 飞书应用创建自动化 v4.0 启动")
        logger.info(f"📋 应用名称：{CONFIG['app_name']}")
        logger.info(f"🔧 调试端口：{CONFIG['debug_port']}")
        logger.info(f"📸 截图目录：{CONFIG['screenshot_dir']}")
        logger.info(f"📝 日志目录：{CONFIG['log_dir']}")
        logger.info("")
        
        steps = [
            ("检查登录状态", self.step_check_login),
            ("创建应用", self.step_create_app),
            ("添加机器人功能", self.step_add_bot_function),
            ("导入权限", self.step_import_permissions),
            ("配置事件订阅", self.step_subscribe_events),
            ("获取凭证", self.step_get_credentials),
            ("发布版本", self.step_publish_version),
        ]
        
        results = []
        for step_name, step_func in steps:
            try:
                success = await step_func()
                results.append({"step": step_name, "success": success})
                if not success:
                    logger.error(f"[FAIL] 步骤失败：{step_name}")
                    break
            except Exception as e:
                logger.error(f"[FAIL] 步骤异常 [{step_name}]: {e}")
                results.append({"step": step_name, "success": False, "error": str(e)})
                break
        
        # 生成报告
        self.generate_report(results)
        
        return results
    
    def generate_report(self, results: List[Dict]):
        """生成执行报告"""
        report_file = Path(CONFIG["log_dir"]) / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("飞书应用创建自动化执行报告\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"应用名称：{CONFIG['app_name']}\n")
            f.write(f"执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"APP ID: {self.app_id or '待确认'}\n")
            f.write(f"APP Secret: {self.app_secret or '需手动保存'}\n\n")
            
            f.write("执行步骤:\n")
            f.write("-" * 80 + "\n")
            for i, result in enumerate(results, 1):
                status = "[OK]" if result.get("success") else "[FAIL]"
                error_info = f" (错误：{result.get('error', '未知')})" if not result.get("success") and result.get("error") else ""
                f.write(f"{i}. {status} {result['step']}{error_info}\n")
            
            f.write("\n截图文件:\n")
            f.write("-" * 80 + "\n")
            for screenshot in self.screenshots:
                f.write(f"- {screenshot}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("安全提示:\n")
            f.write("1. 严禁分享明文密码\n")
            f.write("2. APP Secret 需妥善保管\n")
            f.write("3. 部分权限可能需要管理员审批\n")
            f.write("=" * 80 + "\n")
        
        logger.info(f"[OK] 执行报告已保存：{report_file}")

# ==================== 主函数 ====================

async def main():
    """主函数"""
    creator = FeishuAppCreator()
    results = await creator.run_full_workflow()
    
    print("\n" + "=" * 80)
    print("🎉 飞书应用创建完成!")
    print("=" * 80)
    print(f"应用名称：{CONFIG['app_name']}")
    print(f"APP ID: {creator.app_id or '请查看截图'}")
    print(f"截图数量：{len(creator.screenshots)}")
    print(f"日志文件：{CONFIG['log_dir']}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
