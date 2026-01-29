# mongo_token_bucket.py
import random
import time
from dataclasses import dataclass
from typing import Optional, Tuple

_LUA_WINDOW_LIMITER = """
-- KEYS[1] = window key
-- ARGV[1] = tokens_to_consume
-- ARGV[2] = ttl_seconds
-- ARGV[3] = limit

local tokens = tonumber(ARGV[1])
local ttl = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

local current = redis.call('INCRBY', KEYS[1], tokens)

-- If this was the first increment (key was 0 / nonexistent), set TTL
if current == tokens then
  redis.call('EXPIRE', KEYS[1], ttl)
end

if current <= limit then
  return 1
else
  return 0
end
"""


@dataclass(frozen=True)
class AcquireResult:
    allowed: bool
    retry_after_seconds: int  # for visibility timeout / delay


class MongoTokenBucketManager:
    """
    Window-based limiter:
      - limit tokens per interval_seconds
      - atomic via Redis Lua
    """

    def __init__(
        self,
        redis_manager,
        limit_per_window: int,
        interval_seconds: int = 2,
        bucket_key: str = "global",
        jitter_seconds: Optional[int] = None,
        key_prefix: str = "mongo_write_budget",
    ):
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        if limit_per_window <= 0:
            raise ValueError("limit_per_window must be > 0")

        self.redis = redis_manager
        self.limit = int(limit_per_window)
        self.interval = int(interval_seconds)
        self.bucket_key = bucket_key
        self.key_prefix = key_prefix
        self.jitter = (
            int(jitter_seconds) if jitter_seconds is not None else self.interval
        )  # default: 0..interval

        # Cache the script SHA if you want; eval is fine for now (2-day fix).
        self._lua = _LUA_WINDOW_LIMITER

    def _now(self) -> float:
        return time.time()

    def _window_start(self, now: float) -> int:
        return int(now // self.interval) * self.interval

    def _redis_key(self, window_start: int) -> str:
        return f"{self.key_prefix}:{self.bucket_key}:{window_start}"

    def acquire(self, tokens: int = 1) -> AcquireResult:
        """
        Try to consume tokens. If denied, returns retry_after_seconds to push visibility timeout.
        """
        now = self._now()
        window_start = self._window_start(now)
        window_end = window_start + self.interval

        key = self._redis_key(window_start)

        # TTL a bit bigger than the window so old keys go away safely
        ttl_seconds = max(self.interval * 2, 5)

        allowed = self.redis.eval(
            self._lua,
            numkeys=1,
            keys=[key],
            args=[str(int(tokens)), str(int(ttl_seconds)), str(int(self.limit))],
        )

        if allowed == 1:
            return AcquireResult(allowed=True, retry_after_seconds=0)

        # Denied: retry after next window, plus jitter to avoid waves
        base = max(0.0, window_end - now)  # seconds until next window
        jitter = random.uniform(0.0, float(self.jitter))
        retry_after = int(max(1.0, base + jitter))  # at least 1s

        return AcquireResult(allowed=False, retry_after_seconds=retry_after)
