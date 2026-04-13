"""重试装饰器 + 错误分类"""
import time
import functools
from typing import Callable, Tuple, Optional


class BrowserStepError(Exception):
    """浏览器操作步骤错误基类"""
    def __init__(self, message: str, action: str, selector: str = None,
                 error_type: str = "UNKNOWN"):
        super().__init__(message)
        self.action = action
        self.selector = selector
        self.error_type = error_type


class SelectorNotFound(BrowserStepError):
    """选择器未找到"""
    def __init__(self, selector: str, action: str):
        super().__init__(f"Selector not found: {selector}", action, selector, "SELECTOR_NOT_FOUND")
        self.selector = selector


class NavigationError(BrowserStepError):
    """导航错误（超时/DNS/拒绝连接）"""
    def __init__(self, url: str, original_error: str):
        super().__init__(f"Navigation failed: {original_error}", "nav", url, "NAVIGATION_ERROR")
        self.url = url


class TimeoutError(BrowserStepError):
    """操作超时"""
    def __init__(self, action: str, selector: str, timeout_ms: int):
        super().__init__(f"Timeout after {timeout_ms}ms", action, selector, "TIMEOUT")
        self.timeout_ms = timeout_ms


class BrowserDisconnected(BrowserStepError):
    """浏览器连接断开"""
    def __init__(self, reason: str = ""):
        super().__init__(f"Browser disconnected: {reason}", "connect", None, "BROWSER_DISCONNECTED")
        self.reason = reason


def classify_error(exception: Exception) -> str:
    """从异常对象分类错误类型"""
    name = type(exception).__name__
    msg = str(exception).lower()

    if "selector" in msg or "not found" in msg or "query_selector" in msg:
        return "SELECTOR_NOT_FOUND"
    elif "timeout" in msg or "timed out" in msg:
        return "TIMEOUT"
    elif "navigation" in msg or "net::" in msg or "resolve" in msg:
        return "NAVIGATION_ERROR"
    elif "disconnected" in msg or "close" in msg or "target closed" in msg:
        return "BROWSER_DISCONNECTED"
    elif "authentication" in msg or "401" in msg or "403" in msg:
        return "AUTH_ERROR"
    elif "intercept" in msg or "net::ERR_" in msg:
        return "NETWORK_ERROR"
    return "UNKNOWN"


def retry_on_error(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential: bool = True,
    exceptions: Tuple[type, ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    重试装饰器（专给浏览器操作用）

    参数:
        max_attempts: 最大尝试次数
        base_delay: 初始等待秒数
        max_delay: 最大等待秒数
        exponential: True=指数退避，False=固定等待
        exceptions: 需要重试的异常类型
        on_retry: 每次重试前的回调，签名 (attempt, delay, error) -> None
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt == max_attempts:
                        break
                    if exponential:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    else:
                        delay = base_delay
                    if on_retry:
                        on_retry(attempt, delay, e)
                    time.sleep(delay)
            raise last_error
        return wrapper
    return decorator


def retry_decorator(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exponential: bool = True,
    retriable_types: Tuple[str, ...] = ("TIMEOUT", "SELECTOR_NOT_FOUND", "BROWSER_DISCONNECTED")
):
    """
    基于错误类型的条件重试装饰器

    只对指定错误类型重试，其他错误直接抛出
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except BrowserStepError as e:
                    last_error = e
                    if e.error_type not in retriable_types:
                        raise  # 不重试，直接抛出
                    if attempt == max_attempts:
                        break
                    delay = min(base_delay * (2 ** (attempt - 1)), 10.0)
                    print(f"  [RETRY #{attempt}] {e.error_type}: {str(e)[:60]}, "
                          f"等待 {delay:.1f}s...")
                    time.sleep(delay)
                except Exception as e:
                    err_type = classify_error(e)
                    last_error = e
                    if err_type not in retriable_types:
                        raise
                    if attempt == max_attempts:
                        break
                    delay = min(base_delay * (2 ** (attempt - 1)), 10.0)
                    print(f"  [RETRY #{attempt}] {err_type}: {str(e)[:60]}, "
                          f"等待 {delay:.1f}s...")
                    time.sleep(delay)
            raise last_error
        return wrapper
    return decorator
