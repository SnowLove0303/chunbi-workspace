"""
Human Desktop Agent - 统一入口
组合 browser-use + 屏幕解析，一次任务完成

用法:
    python human_desktop.py <任务>           # 浏览器任务
    python human_desktop.py --screen <任务>   # 屏幕理解
    python human_desktop.py --demo           # 演示模式
"""
import sys
import os
import argparse

# 添加 skill 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def run_browser_task(task: str):
    """运行浏览器任务"""
    import asyncio
    from lib.browser_agent import run_task
    
    async def main():
        print(f"执行浏览器任务: {task}")
        result = await run_task(task, headless=False)
        return result
    
    return asyncio.run(main())


def run_screen_task(task: str):
    """运行屏幕理解任务"""
    from lib.screen_parser import capture_and_describe
    
    print(f"截取屏幕并分析: {task}")
    result = capture_and_describe(task)
    print(f"截图: {result['screenshot']}")
    print(f"描述: {result['description']}")
    return result


def demo():
    """演示模式"""
    print("=" * 60)
    print("Human Desktop Agent 演示")
    print("=" * 60)
    
    # 1. 屏幕截图
    print("\n[1] 屏幕截图...")
    from lib.screen_parser import ScreenParser
    parser = ScreenParser()
    path = parser.capture_screen()
    print(f"    截图保存: {path}")
    
    # 2. 显示窗口
    print("\n[2] 可用窗口列表...")
    from lib.desktop_automation import list_windows
    windows = list_windows()
    for i, w in enumerate(windows[:5]):
        print(f"    {i+1}. {w}")
    
    print("\n演示完成！")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Human Desktop Agent - 真人级桌面控制"
    )
    parser.add_argument('task', nargs='?', help='任务描述')
    parser.add_argument('--screen', action='store_true', help='屏幕理解模式')
    parser.add_argument('--demo', action='store_true', help='演示模式')
    
    args = parser.parse_args()
    
    if args.demo:
        demo()
    elif args.task:
        if args.screen:
            run_screen_task(args.task)
        else:
            result = run_browser_task(args.task)
            print("\n结果:", result)
    else:
        parser.print_help()
