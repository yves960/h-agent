"""
Resilience - 弹性重试和熔断
"""

import time
import random
import threading
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps


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
        """计算重试延迟。"""
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
        
        error_str = str(error).lower()
        retryable = ["rate limit", "timeout", "connection", "500", "502", "503", "504"]
        return any(e in error_str for e in retryable)


def resilient(max_retries: int = 3, base_delay: float = 1.0):
    """弹性调用装饰器。"""
    def decorator(func: Callable) -> Callable:
        policy = RetryPolicy(RetryConfig(max_retries=max_retries, base_delay=base_delay))
        
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
                    time.sleep(delay)
            
            raise last_error
        
        return wrapper
    return decorator


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """熔断器。"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self._lock = threading.Lock()
    
    def record_success(self):
        with self._lock:
            self.failure_count = 0
            self.state = CircuitState.CLOSED
    
    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
    
    def can_execute(self) -> bool:
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    return True
                return False
            
            return True  # HALF_OPEN
    
    def execute(self, func: Callable, *args, **kwargs):
        """通过熔断器执行函数。"""
        if not self.can_execute():
            raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise