import time
from collections import defaultdict, deque

from fastapi import HTTPException


class InMemoryRateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        queue = self._requests[key]
        while queue and now - queue[0] >= self.window_seconds:
            queue.popleft()
        if len(queue) >= self.limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        queue.append(now)
