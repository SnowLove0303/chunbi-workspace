"""
Unified Human Desktop Agent
结合 browser-use + 屏幕解析，实现真人级桌面控制
使用 OpenRouter 作为 LLM 中间层（支持 MiniMax）
"""
import os
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


# MiniMax via OpenRouter 配置
OPENROUTER_API_KEY = "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"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# 直接 MiniMax API（用于非浏览器任务）
MINIMAX_API_KEY = "sk-cp-VmUpM6ECqaSgr33MzjKMQNgy8cFgArOp0CHifxdVi7qsjPUva3I-dmyTkqPreAyS53oSQZzZyCFFLP-bTbgfIXCnaqc7Iv2TJQgsE3fY5ntSxeddnX-XH_o"
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"


@dataclass
class ParsedElement:
    """解析出的屏幕元素"""
    bbox: List[int]  # [x, y, width, height]
    icon_description: str
    is_interactable: bool
    confidence: float = 1.0


class UnifiedAgent:
    """
    统一 Agent：结合 browser-use 浏览器控制 + 屏幕解析
    使用 OpenRouter 路由到 MiniMax
    """
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self._browser_use_available = self._check_browser_use()
        
    def _check_browser_use(self) -> bool:
        """检查 browser-use 是否可用"""
        try:
            import browser_use
            return True
        except ImportError:
            return False
    
    async def run(self, task: str, url: Optional[str] = None) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task: 自然语言任务描述
            url: 可选，打开指定 URL
            
        Returns:
            执行结果
        """
        if not self._browser_use_available:
            return {
                "status": "error",
                "error": "browser-use not installed. Run: pip install browser-use"
            }
        
        try:
            from browser_use import Agent, Browser
            from browser_use.llm.openrouter.chat import ChatOpenRouter
            
            # 初始化浏览器
            self.browser = Browser(headless=self.headless)
            
            # 通过 OpenRouter 使用 MiniMax
            # OpenRouter 支持 MiniMax 模型: minimax/minimax-m2.5:free 或 minimax/minimax-m2.7
            llm = ChatOpenRouter(
                model="minimax/minimax-m2.7",  # 使用 MiniMax M2.7
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
            )
            
            # 创建 Agent
            agent = Agent(
                task=task,
                llm=llm,
                browser=self.browser
            )
            
            # 执行任务
            result = await agent.run()
            
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
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass


class BrowserAgent:
    """纯浏览器自动化 Agent"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        
    async def run(self, task: str) -> Dict[str, Any]:
        """执行浏览器任务"""
        unified = UnifiedAgent(headless=self.headless)
        result = await unified.run(task)
        await unified.close()
        return result
    
    async def open_url(self, url: str) -> Dict[str, Any]:
        """打开指定 URL"""
        return await self.run(f"打开这个网址: {url}")
    
    async def search(self, query: str) -> Dict[str, Any]:
        """搜索"""
        return await self.run(f"在搜索引擎中搜索: {query}")


class ScreenParser:
    """
    屏幕解析器
    使用 PIL 截图 + MiniMax 视觉理解
    """
    
    def __init__(self):
        pass
        
    def capture_screen(self, output_path: Optional[str] = None) -> str:
        """截取当前屏幕"""
        import pyautogui
        import os
        
        if output_path is None:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                output_path = f.name
        
        screenshot = pyautogui.screenshot()
        screenshot.save(output_path)
        return output_path
    
    def parse_screenshot(self, image_path: str) -> List[ParsedElement]:
        """
        解析截图，提取可交互元素
        使用 MiniMax 视觉理解（如果可用）
        """
        import base64
        import json
        import requests
        from PIL import Image
        
        try:
            # 读取图片
            with open(image_path, 'rb') as f:
                img_base64 = base64.b64encode(f.read()).decode()
            
            # 调用 MiniMax 视觉理解
            # 这里可以用 MiniMax 的多模态 API
            # 简化版本先返回空，实际使用时可以增强
            return []
            
        except Exception as e:
            print(f"Parse error: {e}")
            return []
    
    def describe_screen(self, image_path: str, question: str = "描述这个屏幕") -> str:
        """
        用 MiniMax 理解屏幕内容
        """
        import base64
        import requests
        
        try:
            with open(image_path, 'rb') as f:
                img_base64 = base64.b64encode(f.read()).decode()
            
            # MiniMax 视觉理解 API
            # 这里简化处理
            return f"屏幕截图保存在: {image_path}"
            
        except Exception as e:
            return f"Error: {e}"


async def run_browser_task(task: str, headless: bool = False) -> Dict[str, Any]:
    """运行浏览器任务（便捷函数）"""
    agent = UnifiedAgent(headless=headless)
    result = await agent.run(task)
    await agent.close()
    return result


async def run_screen_task(task: str) -> Dict[str, Any]:
    """截屏并理解"""
    parser = ScreenParser()
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        path = f.name
    
    parser.capture_screen(path)
    
    # 用 MiniMax 理解
    description = parser.describe_screen(path, task)
    
    try:
        os.unlink(path)
    except:
        pass
    
    return {
        "status": "success",
        "description": description,
        "screenshot": path
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python unified_agent.py <task>")
        print("Example: python unified_agent.py '打开百度并搜索 AI'")
        sys.exit(1)
    
    task = " ".join(sys.argv[1:])
    
    async def main():
        print(f"执行任务: {task}")
        agent = UnifiedAgent(headless=False)  # 显示浏览器
        result = await agent.run(task)
        print("结果:", result)
        await agent.close()
    
    asyncio.run(main())
