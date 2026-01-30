#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能重试策略模块
实现指数退避重试机制，根据错误类型决定是否重试
"""

import time
import logging
import random
from functools import wraps
from typing import Callable, TypeVar, Any, Optional, Tuple, List

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """重试配置"""
    # 默认配置
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # 基础延迟（秒）
    MAX_DELAY = 30.0  # 最大延迟（秒）
    EXPONENTIAL_BASE = 2  # 指数基数
    JITTER = True  # 是否添加随机抖动


class RetryableError(Exception):
    """可重试的错误"""
    pass


class NonRetryableError(Exception):
    """不可重试的错误"""
    pass


# 可重试的错误类型
RETRYABLE_ERRORS = (
    ConnectionError,
    TimeoutError,
    RetryableError,
)

# 不可重试的错误关键词
NON_RETRYABLE_KEYWORDS = [
    'permission denied',
    'access denied',
    'invalid credentials',
    'authentication failed',
    'not found',
    '404',
    '403',
    '401',
]


def is_retryable_error(error: Exception) -> bool:
    """判断错误是否可重试"""
    # 明确不可重试的错误
    if isinstance(error, NonRetryableError):
        return False

    # 明确可重试的错误
    if isinstance(error, RETRYABLE_ERRORS):
        return True

    # 检查错误消息中的关键词
    error_msg = str(error).lower()
    for keyword in NON_RETRYABLE_KEYWORDS:
        if keyword in error_msg:
            return False

    # 默认可重试
    return True


def calculate_delay(
    attempt: int,
    base_delay: float = RetryConfig.BASE_DELAY,
    max_delay: float = RetryConfig.MAX_DELAY,
    exponential_base: int = RetryConfig.EXPONENTIAL_BASE,
    jitter: bool = RetryConfig.JITTER
) -> float:
    """
    计算重试延迟时间（指数退避 + 随机抖动）

    Args:
        attempt: 当前重试次数（从1开始）
        base_delay: 基础延迟
        max_delay: 最大延迟
        exponential_base: 指数基数
        jitter: 是否添加随机抖动

    Returns:
        延迟时间（秒）
    """
    # 指数退避: delay = base * (exponential_base ^ attempt)
    delay = base_delay * (exponential_base ** (attempt - 1))

    # 限制最大延迟
    delay = min(delay, max_delay)

    # 添加随机抖动（±25%）
    if jitter:
        jitter_range = delay * 0.25
        delay = delay + random.uniform(-jitter_range, jitter_range)

    return max(0, delay)


def retry_with_backoff(
    max_retries: int = RetryConfig.MAX_RETRIES,
    base_delay: float = RetryConfig.BASE_DELAY,
    max_delay: float = RetryConfig.MAX_DELAY,
    retryable_exceptions: Tuple = RETRYABLE_ERRORS,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None
):
    """
    重试装饰器，支持指数退避

    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟
        max_delay: 最大延迟
        retryable_exceptions: 可重试的异常类型
        on_retry: 重试时的回调函数 (attempt, error, delay)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None

            for attempt in range(1, max_retries + 2):  # +2 因为第一次不算重试
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e

                    # 检查是否可重试
                    if not is_retryable_error(e):
                        logger.warning(f"不可重试的错误: {e}")
                        raise

                    # 检查是否还有重试次数
                    if attempt > max_retries:
                        logger.error(f"已达到最大重试次数 ({max_retries}): {e}")
                        raise

                    # 计算延迟
                    delay = calculate_delay(attempt, base_delay, max_delay)

                    logger.info(f"第 {attempt} 次重试，等待 {delay:.2f} 秒后重试: {e}")

                    # 调用回调
                    if on_retry:
                        on_retry(attempt, e, delay)

                    time.sleep(delay)

            # 不应该到达这里
            raise last_error

        return wrapper
    return decorator


class RetryContext:
    """重试上下文管理器"""

    def __init__(
        self,
        max_retries: int = RetryConfig.MAX_RETRIES,
        base_delay: float = RetryConfig.BASE_DELAY,
        max_delay: float = RetryConfig.MAX_DELAY,
        operation_name: str = "operation"
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.operation_name = operation_name
        self.attempt = 0
        self.last_error: Optional[Exception] = None

    def should_retry(self, error: Exception) -> bool:
        """判断是否应该重试"""
        self.last_error = error
        self.attempt += 1

        if not is_retryable_error(error):
            logger.warning(f"{self.operation_name}: 不可重试的错误 - {error}")
            return False

        if self.attempt > self.max_retries:
            logger.error(f"{self.operation_name}: 已达到最大重试次数 ({self.max_retries})")
            return False

        return True

    def wait(self):
        """等待重试延迟"""
        delay = calculate_delay(self.attempt, self.base_delay, self.max_delay)
        logger.info(f"{self.operation_name}: 第 {self.attempt} 次重试，等待 {delay:.2f} 秒")
        time.sleep(delay)

    def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """执行带重试的操作"""
        while True:
            try:
                result = func(*args, **kwargs)
                if self.attempt > 0:
                    logger.info(f"{self.operation_name}: 第 {self.attempt} 次重试成功")
                return result
            except Exception as e:
                if not self.should_retry(e):
                    raise
                self.wait()


class BatchRetryManager:
    """批量重试管理器，用于管理多个URL的重试"""

    def __init__(
        self,
        max_retries: int = RetryConfig.MAX_RETRIES,
        base_delay: float = RetryConfig.BASE_DELAY
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.failed_items: List[Tuple[Any, int, Exception]] = []  # (item, attempts, last_error)

    def add_failed(self, item: Any, error: Exception, attempts: int = 1):
        """添加失败项"""
        if is_retryable_error(error) and attempts <= self.max_retries:
            self.failed_items.append((item, attempts, error))
            logger.debug(f"添加到重试队列: {item} (已尝试 {attempts} 次)")

    def get_retry_batch(self) -> List[Tuple[Any, int]]:
        """获取需要重试的批次"""
        batch = [(item, attempts) for item, attempts, _ in self.failed_items]
        self.failed_items.clear()
        return batch

    def has_pending(self) -> bool:
        """是否有待重试的项"""
        return len(self.failed_items) > 0

    def get_delay_for_attempt(self, attempt: int) -> float:
        """获取指定重试次数的延迟"""
        return calculate_delay(attempt, self.base_delay)
