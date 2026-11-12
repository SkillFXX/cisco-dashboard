import threading
import time
from collections import defaultdict, deque
from fastapi import HTTPException, status


class FailureLimiter:
    """Limite en memoire le nombre d'echecs par cle (ex. identifiant) sur une fenetre glissante."""

    def __init__(self, max_failures: int, window_seconds: int, message: str = "Trop de tentatives."):
        self.message = message
        self.max_failures = max_failures
        self.window = window_seconds
        self._failures: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque:
        q = self._failures[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if not q:
            self._failures.pop(key, None)
        return q

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            q = self._prune(key, now)
            if len(q) >= self.max_failures:
                retry = int(self.window - (now - q[0])) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"{self.message} Réessayez dans {max(1, -(-retry // 60))} min.",
                    headers={"Retry-After": str(retry)},
                )

    def record(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            self._prune(key, now)
            self._failures[key].append(now)
            if len(self._failures) > 10000:
                for k in list(self._failures)[:1000]:
                    self._prune(k, now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)


login_limiter = FailureLimiter(max_failures=8, window_seconds=15 * 60)
register_limiter = FailureLimiter(max_failures=30, window_seconds=60 * 60)
ai_minute_limiter = FailureLimiter(max_failures=8, window_seconds=60, message="Trop de questions d'affilée.")
ai_day_limiter = FailureLimiter(max_failures=150, window_seconds=24 * 3600, message="Limite quotidienne de questions atteinte.")
