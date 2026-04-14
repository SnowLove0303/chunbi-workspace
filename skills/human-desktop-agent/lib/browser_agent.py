"""
Browser Agent - 基于 browser-use 的浏览器自动化
支持 MiniMax / OpenAI / Claude 等 LLM

⚠️ 当前状态：
- browser-use 0.12.6 已安装，Chrome CDP 连接正常
- MiniMax API 会输出 reasoning_content，导致 JSON 解析失败
- 建议：使用 desktop-automation-ultra 做桌面自动化，或等待 browser-use + MiniMax 兼容方案
"""
import os
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass

# MiniMax API（用于非 browser-use 的直接调用）
MINIMAX_API_KEY = os.environ.get(
    "MINIMAX_API_KEY",
    "sk-cp-VmUpM6ECqaSgr33MzjKMQNgy8cFgArOp0CHifxdVi7qsjPUva3I-dmyTkqPreAyS53oSQZzZyCFFLP-bTbgfIXCnaqc7Iv2TJQgsE3fY5ntSxeddnX-XH_o"
)
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"


@dataclass
class BrowserConfig:
    """浏览器配置"""
    headless: bool = False
    # Chrome DevTools Protocol URL（复用已打开的 Chrome）
    cdp_url: Optional[str] = None
    # Chrome 可执行文件路径
    chrome_path: Optional[str] = None
    # 用户数据目录
    user_data_dir: Optional[str] = None
    # 窗口大小
    window_width: int = 1920
    window_height: int = 1080


def make_minimax_client():
    """创建 MiniMax API 客户端（OpenAI 兼容格式）"""
    try:
        from openai import OpenAI
        return OpenAI(
            api_key=MINIMAX_API_KEY,
            base_url=MINIMAX_BASE_URL
        )
    except ImportError:
        return None


async def minimax_chat(prompt: str, model: str = "MiniMax-M2.7") -> str:
    """
    直接调用 MiniMax API（不经过 browser-use）
    
    注意：MiniMax 会同时返回 content 和 reasoning_content
    reasoning_content 包含思考过程
    """
    client = make_minimax_client()
    if not client:
        return "OpenAI SDK not installed"
    
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"


class BrowserAgent:
    """
    浏览器自动化 Agent
    ⚠️ 试验性功能：MiniMax reasoning_content 会干扰 JSON 解析
    """
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._agent = None
        self._browser = None
        
    async def run(self, task: str) -> Dict[str, Any]:
        """
        执行浏览器任务
        
        ⚠️ 注意：由于 MiniMax 的 reasoning_content 格式，
        browser-use 可能会解析失败。建议使用 desktop-automation-ultra
        做实际自动化任务。
        """
        try:
            from browser_use import Agent, Browser
            from browser_use.llm.openai.chat import ChatOpenAI
            
            # 初始化浏览器
            browser_kwargs = {"headless": self.config.headless}
            
            if self.config.cdp_url:
                browser_kwargs["cdp_url"] = self.config.cdp_url
            if self.config.chrome_path:
                browser_kwargs["executable_path"] = self.config.chrome_path
            if self.config.user_data_dir:
                browser_kwargs["user_data_dir"] = self.config.user_data_dir
            
            self._browser = Browser(**browser_kwargs)
            
            # 使用 MiniMax OpenAI 兼容接口
            llm = ChatOpenAI(
                model="MiniMax-M2.7",
                api_key=MINIMAX_API_KEY,
                base_url=MINIMAX_BASE_URL,
            )
            
            self._agent = Agent(
                task=task,
                llm=llm,
                browser=self._browser,
            )
            
            result = await self._agent.run()
            
            return {
                "status": "success",
                "result": str(result)[:500],
                "task": task
            }
            
        except ImportError as e:
            return {
                "status": "error",
                "error": f"Import error: {e}",
                "hint": "pip install browser-use"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "note": "MiniMax reasoning_content may cause JSON parsing issues with browser-use"
            }
    
    async def close(self):
        """关闭浏览器"""
        if self._browser:
            try:
                await self._browser.close()
            except:
                pass


def start_chrome_debug() -> bool:
    """
    启动 Chrome 调试模式
    返回 True 如果成功
    """
    import subprocess
    import os
    
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    debug_port = 9222
    user_data_dir = r"C:\Users\chenz\AppData\Local\Google\Chrome\User Data"
    
    # 检查端口是否已监听
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', debug_port))
    sock.close()
    
    if result == 0:
        print(f"Chrome debug port {debug_port} already listening")
        return True
    
    # 启动 Chrome
    try:
        subprocess.Popen([
            chrome_path,
            f"--remote-debugging-port={debug_port}",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check"
        ], windowsHide=True)
        
        # 等待端口就绪
        import time
        for _ in range(10):
            time.sleep(1)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', debug_port))
            sock.close()
            if result == 0:
                print(f"Chrome debug mode started on port {debug_port}")
                return True
        
        print("Chrome started but debug port not ready")
        return True
        
    except Exception as e:
        print(f"Failed to start Chrome: {e}")
        return False


async def run_task(task: str, headless: bool = False, cdp_url: str = "http://localhost:9222") -> Dict[str, Any]:
    """便捷函数：运行浏览器任务"""
    # 确保 Chrome 调试模式运行
    if cdp_url == "http://localhost:9222":
        start_chrome_debug()
    
    config = BrowserConfig(headless=headless, cdp_url=cdp_url)
    agent = BrowserAgent(config)
    result = await agent.run(task)
    await agent.close()
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python browser_agent.py <任务>")
        print("示例: python browser_agent.py '打开百度并搜索 AI'")
        sys.exit(1)
    
    task = " ".join(sys.argv[1:])
    
    async def main():
        print(f"执行任务: {task}")
        result = await run_task(task)
        print("结果:", result)
    
    asyncio.run(main())
