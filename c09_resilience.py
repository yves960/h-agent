#!/usr/bin/env python3
"""
c09_resilience.py - Resilience (OpenAI Version)

弹性。失败后自动恢复。

三层重试:
  1. 立即重试 (同一 endpoint)
  2. 指数退避重试
  3. 认证轮换 (多个 API key 轮流)

"""

import os
import time
import random
from typing import List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# Retry Strategy
# ============================================================

@dataclass
class RetryConfig:
    """重试配置。"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True


class RetryPolicy:
    """重试策略。"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    def get_delay(self, attempt: int) -> float:
        """计算第 n 次重试的延迟。"""
        delay = min(
            self.config.base_delay * (2 ** attempt),
            self.config.max_delay
        )
        if self.config.jitter:
            delay *= random.uniform(0.5, 1.5)
        return delay
    
    def should_retry(self, attempt: int, error: Exception) -> bool:
        """判断是否应该重试。"""
        if attempt >= self.config.max_retries:
            return False
        
        # 检查错误类型
        error_str = str(error).lower()
        retryable_errors = [
            "rate limit",
            "timeout",
            "connection",
            "overloaded",
            "500",
            "502",
            "503",
            "504",
        ]
        
        return any(e in error_str for e in retryable_errors)


# ============================================================
# API Key Rotation
# ============================================================

@dataclass
class APIKey:
    """API Key。"""
    key: str
    base_url: str = ""
    healthy: bool = True
    last_used: float = 0
    error_count: int = 0


class KeyRotation:
    """API Key 轮换。"""
    
    def __init__(self):
        self.keys: List[APIKey] = []
        self._current_index = 0
    
    def add_key(self, key: str, base_url: str = ""):
        """添加 API Key。"""
        self.keys.append(APIKey(key=key, base_url=base_url))
    
    def get_next(self) -> Optional[APIKey]:
        """获取下一个可用的 Key。"""
        if not self.keys:
            return None
        
        # 尝试找到健康的 Key
        for _ in range(len(self.keys)):
            api_key = self.keys[self._current_index]
            self._current_index = (self._current_index + 1) % len(self.keys)
            
            if api_key.healthy:
                api_key.last_used = time.time()
                return api_key
        
        # 所有 Key 都不健康，返回第一个并重置健康状态
        self.keys[0].healthy = True
        return self.keys[0]
    
    def mark_error(self, key: str):
        """标记 Key 出错。"""
        for api_key in self.keys:
            if api_key.key == key:
                api_key.error_count += 1
                if api_key.error_count >= 3:
                    api_key.healthy = False
    
    def mark_success(self, key: str):
        """标记 Key 成功。"""
        for api_key in self.keys:
            if api_key.key == key:
                api_key.error_count = 0
                api_key.healthy = True


# ============================================================
# Resilient Client
# ============================================================

class ResilientClient:
    """弹性客户端。"""
    
    def __init__(self):
        self.key_rotation = KeyRotation()
        self.retry_policy = RetryPolicy()
        self._client: Optional[OpenAI] = None
        self._current_key: Optional[APIKey] = None
    
    def add_key(self, key: str, base_url: str = ""):
        """添加 API Key。"""
        self.key_rotation.add_key(key, base_url)
    
    def _get_client(self) -> Optional[OpenAI]:
        """获取客户端。"""
        api_key = self.key_rotation.get_next()
        if not api_key:
            return None
        
        self._current_key = api_key
        return OpenAI(
            api_key=api_key.key,
            base_url=api_key.base_url or None,
        )
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        弹性调用。
        
        Args:
            func: 要调用的函数
            *args, **kwargs: 函数参数
        
        Returns:
            函数返回值
        
        Raises:
            最后一次错误（如果所有重试都失败）
        """
        last_error = None
        
        for attempt in range(self.retry_policy.config.max_retries + 1):
            client = self._get_client()
            if not client:
                raise RuntimeError("No API keys available")
            
            try:
                result = func(client, *args, **kwargs)
                self.key_rotation.mark_success(self._current_key.key)
                return result
            
            except Exception as e:
                last_error = e
                self.key_rotation.mark_error(self._current_key.key)
                
                if not self.retry_policy.should_retry(attempt, e):
                    raise
                
                delay = self.retry_policy.get_delay(attempt)
                print(f"Attempt {attempt + 1} failed, retrying in {delay:.1f}s: {e}")
                time.sleep(delay)
        
        raise last_error


# ============================================================
# Decorator
# ============================================================

def resilient(max_retries: int = 3, base_delay: float = 1.0):
    """弹性调用装饰器。"""
    def decorator(func: Callable) -> Callable:
        policy = RetryPolicy(RetryConfig(
            max_retries=max_retries,
            base_delay=base_delay,
        ))
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    if not policy.should_retry(attempt, e):
                        raise
                    
                    delay = policy.get_delay(attempt)
                    print(f"Retry {attempt + 1}/{max_retries} after {delay:.1f}s")
                    time.sleep(delay)
            
            raise last_error
        
        return wrapper
    return decorator


# ============================================================
# Circuit Breaker
# ============================================================

class CircuitState(Enum):
    CLOSED = "closed"  # 正常
    OPEN = "open"      # 熔断
    HALF_OPEN = "half_open"  # 半开


class CircuitBreaker:
    """熔断器。"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
    
    def record_success(self):
        """记录成功。"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def record_failure(self):
        """记录失败。"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def can_execute(self) -> bool:
        """是否可以执行。"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # 检查是否可以进入半开状态
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        
        # HALF_OPEN: 允许一次尝试
        return True


# ============================================================
# Main
# ============================================================

def main():
    print(f"\033[36mOpenAI Agent Harness - c09 (Resilience)\033[0m")
    
    # 测试重试策略
    policy = RetryPolicy()
    print("\n=== 重试延迟测试 ===")
    for i in range(5):
        delay = policy.get_delay(i)
        print(f"  Attempt {i}: delay = {delay:.2f}s")
    
    # 测试熔断器
    print("\n=== 熔断器测试 ===")
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5.0)
    
    for i in range(5):
        cb.record_failure()
        print(f"  Failure {i+1}: state = {cb.state.value}")
    
    print(f"  Can execute: {cb.can_execute()}")
    
    # 测试装饰器
    print("\n=== 弹性装饰器测试 ===")
    
    call_count = 0
    
    @resilient(max_retries=3, base_delay=0.1)
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Simulated failure")
        return "Success!"
    
    result = flaky_function()
    print(f"  Result: {result} (after {call_count} calls)")
    
    print("\n✅ c09 测试通过")


if __name__ == "__main__":
    main()