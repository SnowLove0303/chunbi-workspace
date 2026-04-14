"""
Browser Task Runner
运行浏览器自动化任务
"""
import sys
import os

# 添加 skill 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.unified_agent import run_browser_task
import asyncio


async def main():
    if len(sys.argv) < 2:
        print("用法: python run_browser_task.py <任务描述>")
        print("示例: python run_browser_task.py '打开百度并搜索 AI'")
        return
    
    task = " ".join(sys.argv[1:])
    print(f"执行任务: {task}")
    
    result = await run_browser_task(task, headless=False)
    print("\n结果:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
