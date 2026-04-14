"""
浏览器管理工具

功能：
1. 启动和管理浏览器实例
2. 复用已登录的浏览器会话
3. 多店铺账号切换
4. 反检测配置
"""

import os
import sys
import time
import socket
from loguru import logger

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    logger.warning("Playwright 未安装，请先运行：pip install playwright")


class BrowserManager:
    """浏览器管理器"""

    def __init__(self, browser_type="edge", headless=False, user_data_dir=None, port=9222):
        """
        初始化浏览器管理器
        
        Args:
            browser_type: 浏览器类型 (chrome / edge / firefox)
            headless: 是否无头模式
            user_data_dir: 用户数据目录（用于保存登录状态）
            port: 远程调试端口
        """
        self.browser_type = browser_type
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.port = port
        self.browser = None
        self.page = None
        self.playwright = None

    def start(self):
        """
        启动浏览器
        
        Returns:
            bool: 是否启动成功
        """
        try:
            self.playwright = sync_playwright().start()
            
            # 获取浏览器类型
            browser_factory = getattr(self.playwright, self.browser_type, self.playwright.chromium)
            
            # 构建启动参数
            launch_args = {
                "headless": self.headless,
            }
            
            # 如果有用户数据目录，启用持久化会话
            if self.user_data_dir:
                os.makedirs(self.user_data_dir, exist_ok=True)
                launch_args["args"] = [
                    f"--user-data-dir={os.path.abspath(self.user_data_dir)}",
                    f"--remote-debugging-port={self.port}",
                    "--disable-blink-features=AutomationControlled",  # 反检测
                ]
                
                # 其他反检测参数
                launch_args["args"].extend([
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                ])
            
            # 启动浏览器
            self.browser = browser_factory.launch(**launch_args)
            
            # 创建新页面
            self.page = self.browser.new_page()
            
            # 设置反检测
            self._setup_anti_detection()
            
            logger.info(f"浏览器已启动：{self.browser_type}, 端口：{self.port}")
            
            return True
            
        except Exception as e:
            logger.error(f"启动浏览器失败：{e}")
            return False

    def _setup_anti_detection(self):
        """设置反检测"""
        try:
            # 注入 JavaScript 隐藏自动化特征
            self.page.add_init_script("""
                // 隐藏 WebDriver 特征
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // 修改 navigator.plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // 修改 navigator.languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh']
                });
            """)
            
            logger.debug("反检测脚本已注入")
            
        except Exception as e:
            logger.warning(f"设置反检测失败：{e}")

    def navigate(self, url, timeout=60000):
        """
        导航到指定 URL
        
        Args:
            url: 目标 URL
            timeout: 超时时间（毫秒）
            
        Returns:
            bool: 是否成功
        """
        if not self.page:
            logger.error("浏览器未启动")
            return False
        
        try:
            self.page.goto(url, timeout=timeout)
            logger.debug(f"已导航到：{url}")
            return True
            
        except Exception as e:
            logger.error(f"导航失败：{e}")
            return False

    def wait_for_login(self, check_url_pattern, timeout=120000):
        """
        等待用户登录
        
        Args:
            check_url_pattern: 用于检查登录成功的 URL 模式
            timeout: 超时时间（毫秒）
            
        Returns:
            bool: 是否登录成功
        """
        try:
            logger.info("等待用户登录...")
            self.page.wait_for_url(check_url_pattern, timeout=timeout)
            logger.info("登录成功")
            return True
            
        except Exception as e:
            logger.error(f"登录超时：{e}")
            return False

    def is_logged_in(self, check_url):
        """
        检查是否已登录
        
        Args:
            check_url: 需要登录才能访问的 URL
            
        Returns:
            bool: 是否已登录
        """
        if not self.page:
            return False
        
        try:
            self.page.goto(check_url, timeout=30000)
            time.sleep(2)
            
            # 检查当前 URL 是否包含登录相关关键词
            current_url = self.page.url.lower()
            if "login" in current_url or "signin" in current_url:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"检查登录状态失败：{e}")
            return False

    def screenshot(self, filepath):
        """
        截取屏幕截图
        
        Args:
            filepath: 保存路径
            
        Returns:
            bool: 是否成功
        """
        if not self.page:
            return False
        
        try:
            self.page.screenshot(path=filepath)
            logger.info(f"截图已保存：{filepath}")
            return True
            
        except Exception as e:
            logger.error(f"截图失败：{e}")
            return False

    def close(self):
        """关闭浏览器"""
        try:
            if self.browser:
                self.browser.close()
                logger.info("浏览器已关闭")
            
            if self.playwright:
                self.playwright.stop()
                
        except Exception as e:
            logger.error(f"关闭浏览器失败：{e}")

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


def check_port_available(port):
    """
    检查端口是否可用
    
    Args:
        port: 端口号
        
    Returns:
        bool: 是否可用
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("localhost", port))
            return True
    except:
        return False


def find_chrome_port():
    """
    查找已打开的 Chrome/Edge 浏览器端口
    
    Returns:
        int: 找到的端口号，如果没有找到返回 None
    """
    # 常见端口范围
    for port in range(9222, 9230):
        if check_port_available(port):
            continue
        else:
            logger.info(f"发现已占用的浏览器端口：{port}")
            return port
    
    return None


if __name__ == "__main__":
    # 测试
    print("\n=== 浏览器管理测试 ===\n")
    
    # 检查端口
    print(f"端口 9222 可用：{check_port_available(9222)}")
    
    # 查找已打开的浏览器
    port = find_chrome_port()
    if port:
        print(f"找到浏览器端口：{port}")
    else:
        print("未找到已打开的浏览器")
    
    # 测试启动浏览器
    with BrowserManager(
        browser_type="chromium",
        headless=False,
        user_data_dir="./browser_data/test",
        port=9222
    ) as manager:
        manager.navigate("https://www.baidu.com")
        time.sleep(2)
        manager.screenshot("./test_screenshot.png")
        print("测试完成")
