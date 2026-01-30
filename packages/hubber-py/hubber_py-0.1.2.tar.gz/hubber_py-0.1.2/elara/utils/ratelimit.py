import asyncio
from time import perf_counter
from typing import Optional


class RateLimiter:
    __slots__ = ('max_calls', 'period', '_tokens', '_last_update', '_lock', '_waiters')
    
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self._tokens = float(max_calls)
        self._last_update = perf_counter()
        self._lock = asyncio.Lock()
        self._waiters = 0
    
    async def acquire(self, tokens: int = 1) -> None:
        async with self._lock:
            self._waiters += 1
            try:
                while True:
                    now = perf_counter()
                    elapsed = now - self._last_update
                    self._tokens = min(self.max_calls, self._tokens + elapsed * (self.max_calls / self.period))
                    self._last_update = now
                    
                    if self._tokens >= tokens:
                        self._tokens -= tokens
                        return
                    
                    deficit = tokens - self._tokens
                    sleep_time = deficit * (self.period / self.max_calls)
                    await asyncio.sleep(sleep_time)
            finally:
                self._waiters -= 1
    
    def get_tokens(self) -> float:
        now = perf_counter()
        elapsed = now - self._last_update
        return min(self.max_calls, self._tokens + elapsed * (self.max_calls / self.period))
    
    def get_wait_time(self, tokens: int = 1) -> float:
        available = self.get_tokens()
        if available >= tokens:
            return 0.0
        deficit = tokens - available
        return deficit * (self.period / self.max_calls)
