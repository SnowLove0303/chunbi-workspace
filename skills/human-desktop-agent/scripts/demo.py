"""
Demo - 演示 browser-use + OmniParser 组合
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.unified_agent import ScreenParser, BrowserAgent
import asyncio


async def demo_browser():
    """演示浏览器自动化"""
    print("=" * 50)
    print("演示1: 浏览器自动化")
    print("=" * 50)
    
    agent = BrowserAgent(headless=False)
    result = await agent.open_url("https://www.baidu.com")
    print("打开百度:", result)


def demo_screen_parse():
    """演示屏幕解析"""
    print("\n" + "=" * 50)
    print("演示2: 屏幕解析")
    print("=" * 50)
    
    parser = ScreenParser()
    
    # 截取屏幕
    path = parser.capture_screen()
    print(f"截图保存到: {path}")
    
    # 解析元素
    elements = parser.parse_screenshot(path)
    print(f"找到 {len(elements)} 个可交互元素")
    
    return path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Human Desktop Agent Demo')
    parser.add_argument('mode', choices=['browser', 'screen', 'all'], 
                        default='all', nargs='?',
                        help='演示模式: browser(浏览器) / screen(屏幕解析) / all(全部)')
    args = parser.parse_args()
    
    if args.mode in ['browser', 'all']:
        asyncio.run(demo_browser())
    
    if args.mode in ['screen', 'all']:
        demo_screen_parse()
