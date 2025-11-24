"""
Orchestrator Utilities

提供重試機制、錯誤處理等工具函數。
"""

import time
import logging
from typing import Callable, Any, Type
from functools import wraps

logger = logging.getLogger(__name__)


def is_retriable_error(error: Exception) -> bool:
    """
    判斷錯誤是否可重試

    可重試錯誤類型：
    - 網絡超時 (TimeoutError, requests.Timeout)
    - API 臨時不可用 (HTTPError 503, 502, 504)
    - Rate Limit (HTTPError 429)
    - 連接錯誤 (ConnectionError)

    不可重試錯誤類型：
    - 認證失敗 (HTTPError 401, 403)
    - 資源不存在 (HTTPError 404)
    - 參數錯誤 (HTTPError 400)
    - ValueError, TypeError 等程式錯誤

    Args:
        error: 異常對象

    Returns:
        bool: 是否可重試
    """
    error_str = str(error).lower()
    error_type = type(error).__name__

    # 網絡相關錯誤
    if error_type in ["TimeoutError", "ConnectionError", "Timeout"]:
        return True

    # HTTP 錯誤
    if "HTTPError" in error_type or "http" in error_str:
        # 檢查狀態碼
        if any(code in error_str for code in ["429", "500", "502", "503", "504"]):
            return True
        # 明確不可重試的狀態碼
        if any(code in error_str for code in ["400", "401", "403", "404"]):
            return False

    # API 錯誤
    if "api" in error_str and any(word in error_str for word in ["timeout", "unavailable", "rate limit"]):
        return True

    # 程式邏輯錯誤（不可重試）
    if error_type in ["ValueError", "TypeError", "KeyError", "AttributeError"]:
        return False

    # 預設不重試（保守策略）
    return False


def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    retriable_exceptions: tuple = (Exception,)
):
    """
    指數退避重試裝飾器

    Args:
        max_retries: 最大重試次數（不包括首次嘗試）
        backoff_factor: 退避因子（每次重試延遲倍數）
        initial_delay: 初始延遲秒數
        max_delay: 最大延遲秒數
        retriable_exceptions: 可重試的異常類型元組

    Returns:
        裝飾器函數

    Example:
        @retry_with_backoff(max_retries=3, backoff_factor=2)
        def fetch_data():
            response = requests.get("https://api.example.com/data")
            return response.json()

        # 首次嘗試失敗，依次延遲 1s, 2s, 4s 後重試
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay

            for attempt in range(max_retries + 1):  # +1 包含首次嘗試
                try:
                    return func(*args, **kwargs)

                except retriable_exceptions as e:
                    # 最後一次嘗試，直接拋出異常
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries + 1} attempts")
                        raise

                    # 判斷是否可重試
                    if not is_retriable_error(e):
                        logger.warning(f"Non-retriable error in {func.__name__}: {e}")
                        raise

                    # 計算延遲時間
                    wait_time = min(delay, max_delay)
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )

                    time.sleep(wait_time)
                    delay *= backoff_factor

        return wrapper
    return decorator


def retry_on_condition(
    condition: Callable[[Any], bool],
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0
):
    """
    基於返回值條件的重試裝飾器

    Args:
        condition: 判斷是否需要重試的函數（返回 True 表示需要重試）
        max_retries: 最大重試次數
        backoff_factor: 退避因子
        initial_delay: 初始延遲秒數

    Returns:
        裝飾器函數

    Example:
        @retry_on_condition(lambda result: result["status"] != "success", max_retries=3)
        def fetch_data():
            return api_call()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay

            for attempt in range(max_retries + 1):
                result = func(*args, **kwargs)

                # 檢查是否需要重試
                if not condition(result):
                    return result

                # 最後一次嘗試
                if attempt == max_retries:
                    logger.warning(f"Function {func.__name__} did not meet condition after {max_retries + 1} attempts")
                    return result

                # 重試
                logger.info(f"Attempt {attempt + 1} failed condition check, retrying in {delay:.1f}s...")
                time.sleep(delay)
                delay *= backoff_factor

            return result

        return wrapper
    return decorator


class RetryStrategy:
    """
    重試策略類（用於非裝飾器場景）

    Example:
        retry_strategy = RetryStrategy(max_retries=3, backoff_factor=2)

        for attempt in retry_strategy:
            try:
                result = api_call()
                break  # 成功，跳出重試
            except Exception as e:
                if not retry_strategy.should_retry(e):
                    raise
                # 繼續重試
    """

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 60.0
    ):
        """
        初始化重試策略

        Args:
            max_retries: 最大重試次數
            backoff_factor: 退避因子
            initial_delay: 初始延遲秒數
            max_delay: 最大延遲秒數
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay
        self.max_delay = max_delay

        self.attempt = 0
        self.delay = initial_delay

    def __iter__(self):
        """使類可迭代"""
        return self

    def __next__(self):
        """返回下一次嘗試"""
        if self.attempt > self.max_retries:
            raise StopIteration

        # 第一次嘗試不延遲
        if self.attempt > 0:
            wait_time = min(self.delay, self.max_delay)
            logger.info(f"Retrying in {wait_time:.1f}s... (attempt {self.attempt + 1}/{self.max_retries + 1})")
            time.sleep(wait_time)
            self.delay *= self.backoff_factor

        self.attempt += 1
        return self.attempt

    def should_retry(self, error: Exception) -> bool:
        """
        判斷是否應該重試

        Args:
            error: 異常對象

        Returns:
            bool: 是否應該重試
        """
        # 已達到最大重試次數
        if self.attempt > self.max_retries:
            return False

        # 判斷錯誤是否可重試
        return is_retriable_error(error)

    def reset(self):
        """重置重試狀態"""
        self.attempt = 0
        self.delay = self.initial_delay


def execute_with_timeout(func: Callable, timeout_seconds: float, *args, **kwargs) -> Any:
    """
    在指定時間內執行函數（使用 threading）

    注意：此函數使用 threading，適用於 I/O 密集型操作。
    對於 CPU 密集型操作，建議使用 multiprocessing。

    Args:
        func: 要執行的函數
        timeout_seconds: 超時秒數
        *args: 函數位置參數
        **kwargs: 函數關鍵字參數

    Returns:
        函數執行結果

    Raises:
        TimeoutError: 如果執行超時

    Example:
        result = execute_with_timeout(slow_function, 10, arg1, arg2, key=value)
    """
    import threading

    result = [None]
    exception = [None]

    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)

    if thread.is_alive():
        logger.error(f"Function {func.__name__} timed out after {timeout_seconds}s")
        raise TimeoutError(f"Function execution exceeded {timeout_seconds}s")

    if exception[0]:
        raise exception[0]

    return result[0]


if __name__ == "__main__":
    # 測試範例
    import requests

    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def test_api_call():
        """測試 API 調用（會失敗 2 次）"""
        print("Calling API...")
        # 模擬前 2 次失敗
        import random
        if random.random() < 0.7:
            raise ConnectionError("Network timeout")
        return {"status": "success"}

    try:
        result = test_api_call()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")
