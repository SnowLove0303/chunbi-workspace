"""
Browser Agent - 基于 browser-use 的浏览器自动化
支持 MiniMax / OpenAI / Claude 等 LLM
"""
import os
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass

# OpenRouter API（路由 MiniMax）
OPENROUTER_API_KEY = os.environ.get(
    "OPENROUTER_API_KEY",
    "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"
)
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


@dataclass
class BrowserConfig:
    """浏览器配置"""
    headless: bool = False
    headless_delay: float = 2.0
    # Chrome DevTools Protocol URL（复用已打开的 Chrome）
    cdp_url: Optional[str] = None
    # Chrome 可执行文件路径
    chrome_path: Optional[str] = None
    # 用户数据目录（复用 Chrome Profile）
    user_data_dir: Optional[str] = None
    # 窗口大小
    window_width: int = 1920
    window_height: int = 1080


class BrowserAgent:
    """
    浏览器自动化 Agent
    使用 browser-use + OpenRouter(MiniMax)
    """
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._agent = None
        self._browser = None
        
    async def run(self, task: str) -> Dict[str, Any]:
        """
        执行浏览器任务
        
        Args:
            task: 自然语言任务描述
            Examples:
                "打开百度并搜索 AI"
                "登录 GitHub"
                "填写这个表单"
        """
        try:
            from browser_use import Agent, Browser
            from browser_use.llm.openrouter.chat import ChatOpenRouter
            
            # 初始化浏览器
            browser_kwargs = {
                "headless": self.config.headless,
                "headless_delay": self.config.headless_delay,
            }
            
            # 如果指定了 CDP URL（复用已打开的 Chrome）
            if self.config.cdp_url:
                browser_kwargs["cdp_url"] = self.config.cdp_url
            elif self.config.chrome_path:
                browser_kwargs["chrome_path"] = self.config.chrome_path
            elif self.config.user_data_dir:
                browser_kwargs["user_data_dir"] = self.config.user_data_dir
            
            self._browser = Browser(**browser_kwargs)
            
            # 初始化 LLM（通过 OpenRouter 使用 MiniMax）
            llm = ChatOpenRouter(
                model="minimax/minimax-m2.7",
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
            )
            
            # 创建 Agent
            self._agent = Agent(
                task=task,
                llm=llm,
                browser=self._browser,
            )
            
            # 执行任务
            result = await self._agent.run()
            
            return {
                "status": "success",
                "result": result,
                "task": task
            }
            
        except ImportError as e:
            return {
                "status": "error",
                "error": f"Import error: {e}",
                "hint": "Install browser-use: pip install browser-use"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def close(self):
        """关闭浏览器"""
        if self._browser:
            try:
                await self._browser.close()
            except:
                pass


async def run_task(task: str, headless: bool = False) -> Dict[str, Any]:
    """便捷函数：运行浏览器任务"""
    config = BrowserConfig(headless=headless)
    agent = BrowserAgent(config)
    result = await agent.run(task)
    await agent.close()
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python browser_agent.py <task>")
        sys.exit(1)
    
    task = " ".join(sys.argv[1:])
    
    async def main():
        print(f"执行任务: {task}")
        result = await run_task(task, headless=False)
        print("结果:", result)
    
    asyncio.run(main())
