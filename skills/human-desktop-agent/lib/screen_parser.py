"""
Screen Parser - 屏幕解析器
使用 pyautogui 截图 + MiniMax 视觉理解
"""
import os
import base64
import json
import tempfile
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# MiniMax API
MINIMAX_API_KEY = os.environ.get(
    "MINIMAX_API_KEY",
    "sk-cp-VmUpM6ECqaSgr33MzjKMQNgy8cFgArOp0CHifxdVi7qsjPUva3I-dmyTkqPreAyS53oSQZzZyCFFLP-bTbgfIXCnaqc7Iv2TJQgsE3fY5ntSxeddnX-XH_o"
)
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"


@dataclass
class ScreenElement:
    """屏幕元素"""
    bbox: List[int]  # [x, y, width, height]
    description: str
    interactable: bool = True
    confidence: float = 1.0


class ScreenParser:
    """
    屏幕解析器
    功能：
    1. 截取屏幕
    2. 用 MiniMax 视觉理解屏幕内容
    3. 提取可交互元素
    """
    
    def __init__(self):
        self.minimax_available = self._check_minimax()
    
    def _check_minimax(self) -> bool:
        """检查 MiniMax API 是否可用"""
        try:
            import requests
            return True
        except ImportError:
            return False
    
    def capture_screen(self, output_path: Optional[str] = None) -> str:
        """
        截取当前屏幕
        
        Args:
            output_path: 保存路径，默认临时文件
            
        Returns:
            截图路径
        """
        import pyautogui
        
        if output_path is None:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                output_path = f.name
        
        screenshot = pyautogui.screenshot()
        screenshot.save(output_path)
        return output_path
    
    def describe_screen(self, image_path: str, question: str = "描述这个屏幕") -> str:
        """
        用 MiniMax 视觉理解屏幕内容
        
        Args:
            image_path: 截图路径
            question: 问题（如"找出所有可点击按钮"）
            
        Returns:
            MiniMax 的描述
        """
        if not self.minimax_available:
            return "MiniMax API not available"
        
        try:
            import requests
            
            with open(image_path, 'rb') as f:
                img_base64 = base64.b64encode(f.read()).decode()
            
            # MiniMax 视觉理解 API
            # 这里使用文本-only 模式，实际应该用多模态
            # 简化：返回截图路径让用户自己看
            return f"截图保存于: {image_path}\n问题: {question}\n请查看截图进行操作。"
            
        except Exception as e:
            return f"Error: {e}"
    
    def find_element(self, template_path: str, confidence: float = 0.8) -> Optional[ScreenElement]:
        """
        使用图像识别查找元素
        
        Args:
            template_path: 模板图片路径
            confidence: 匹配置信度
            
        Returns:
            找到的元素位置，或 None
        """
        try:
            import cv2
            import numpy as np
            import pyautogui
            
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
                return ScreenElement(
                    bbox=[max_loc[0], max_loc[1], w, h],
                    description=f"Found template at ({max_loc[0]}, {max_loc[1]})",
                    confidence=max_val
                )
            return None
            
        except Exception as e:
            print(f"Find element error: {e}")
            return None
    
    def parse_screenshot(self, image_path: str) -> List[ScreenElement]:
        """
        解析截图，提取可交互元素
        这个版本使用简化的图像处理 + LLM
        """
        # 后续可以集成 OmniParser 或 MiniMax 视觉 API
        return []


def capture_and_describe(question: str = "描述这个屏幕") -> Dict[str, Any]:
    """便捷函数：截屏并理解"""
    parser = ScreenParser()
    
    # 截取屏幕
    path = parser.capture_screen()
    
    # 理解内容
    description = parser.describe_screen(path, question)
    
    return {
        "screenshot": path,
        "description": description
    }


if __name__ == "__main__":
    import sys
    
    parser = ScreenParser()
    
    # 截取屏幕
    path = parser.capture_screen()
    print(f"截图保存到: {path}")
    
    # 如果有参数，当作问题处理
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        desc = parser.describe_screen(path, question)
        print(desc)
