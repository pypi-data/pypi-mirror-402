import random
import time
from dataclasses import dataclass
from typing import Optional, Tuple

from reach_commons.redis_manager import RedisManager

# Atomic fixed-window limiter (safe under high concurrency).
_LUA_WINDOW_LIMITER = """
-- KEYS[1] = window_counter_key
-- ARGV[1] = tokens_to_consume
-- ARGV[2] = ttl_seconds
-- ARGV[3] = limit_per_window

local tokens = tonumber(ARGV[1])
local ttl = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

local current = redis.call('INCRBY', KEYS[1], tokens)

-- If this is the first increment for this window, set TTL
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
    retry_after_seconds: int


class ReachRateLimiter:
    """
    ReachRateLimiter (fixed-window limiter) backed by Redis.

    Configurable live via Redis (no redeploy needed).
    Atomic under heavy concurrency (Lua runs inside Redis).
    Returns retry_after_seconds (use it to ChangeMessageVisibility / Delay).

    Redis keys used:
      - Config hash:
          {key_prefix}:cfg:{bucket_key}
        Fields (all optional):
          - limit_per_window (int)
          - interval_seconds (int)
          - jitter_seconds (int)

      - Per-window counter:
          {key_prefix}:{bucket_key}:{window_start}

    Suggested defaults:
      interval_seconds=2
      limit_per_window=2000 (=> ~1000/s)
      jitter_seconds=2 or 3
    """

    def __init__(
        self,
        redis_manager: RedisManager,
        bucket_key: str,
        key_prefix: str = "rate_limiter",
        default_limit_per_window: int = 2000,
        default_interval_seconds: int = 2,
        default_jitter_seconds: Optional[int] = None,
        # Cache config in-memory per Lambda container (to reduce Redis reads):
        config_cache_seconds: int = 2,
        # if Redis is down, deny by default to avoid stampede downstream
        deny_on_redis_error: bool = True,
    ):
        self.redis = redis_manager
        self.bucket_key = bucket_key
        self.key_prefix = key_prefix

        self.default_limit = int(default_limit_per_window)
        self.default_interval = int(default_interval_seconds)
        self.default_jitter = (
            int(default_jitter_seconds)
            if default_jitter_seconds is not None
            else int(default_interval_seconds)
        )

        self.config_cache_seconds = max(0, int(config_cache_seconds))
        self.deny_on_redis_error = bool(deny_on_redis_error)

        self._lua = _LUA_WINDOW_LIMITER

        # Per-container cache (each Lambda container caches for a short time)
        self._cached_cfg: Optional[Tuple[int, int, int]] = None
        self._cached_cfg_ts: float = 0.0

    # -------------------------
    # Redis key helpers
    # -------------------------
    def _cfg_key(self) -> str:
        return f"{self.key_prefix}:cfg:{self.bucket_key}"

    def _counter_key(self, window_start: int) -> str:
        return f"{self.key_prefix}:{self.bucket_key}:{window_start}"

    # -------------------------
    # Time helpers
    # -------------------------
    def _now(self) -> float:
        return time.time()

    def _window_start(self, now: float, interval_seconds: int) -> int:
        return int(now // interval_seconds) * interval_seconds

    # -------------------------
    # Config loading (from Redis hash)
    # -------------------------
    @staticmethod
    def _parse_int(value, fallback: int) -> int:
        try:
            if value is None:
                return fallback
            if isinstance(value, (bytes, bytearray)):
                value = value.decode("utf-8", errors="ignore")
            return int(value)
        except Exception:
            return fallback

    def _load_config(self) -> Tuple[int, int, int]:
        """
        Loads config from Redis hash:
          limit_per_window, interval_seconds, jitter_seconds

        Behavior:
          - If config exists in Redis: read only (never overwrite).
          - If config does NOT exist yet: seed Redis ONCE with defaults (so you can edit live).
          - If Redis is unavailable: fallback to defaults (no writes).
        """
        now = self._now()

        if (
            self._cached_cfg is not None
            and self.config_cache_seconds > 0
            and (now - self._cached_cfg_ts) < self.config_cache_seconds
        ):
            return self._cached_cfg

        limit = self.default_limit
        interval = self.default_interval
        jitter = self.default_jitter

        try:
            cfg_key = self._cfg_key()
            raw = self.redis.hgetall(cfg_key) or {}

            # If config was never created, seed it once with defaults
            if not raw:
                rc = self.redis.redis_connection
                rc.hsetnx(cfg_key, "limit_per_window", str(self.default_limit))
                rc.hsetnx(cfg_key, "interval_seconds", str(self.default_interval))
                rc.hsetnx(cfg_key, "jitter_seconds", str(self.default_jitter))

                # Re-read after seeding (so we now depend on Redis config)
                raw = self.redis.hgetall(cfg_key) or {}

            # raw typically has bytes keys/values
            limit = self._parse_int(
                raw.get(b"limit_per_window") or raw.get("limit_per_window"), limit
            )
            interval = self._parse_int(
                raw.get(b"interval_seconds") or raw.get("interval_seconds"), interval
            )
            jitter = self._parse_int(
                raw.get(b"jitter_seconds") or raw.get("jitter_seconds"), jitter
            )

            # If someone puts garbage in Redis
            if limit <= 0:
                limit = self.default_limit
            if interval <= 0:
                interval = self.default_interval
            if jitter < 0:
                jitter = 0

        except Exception:
            # Redis issue: keep defaults
            limit = self.default_limit
            interval = self.default_interval
            jitter = self.default_jitter

        cfg = (int(limit), int(interval), int(jitter))
        self._cached_cfg = cfg
        self._cached_cfg_ts = now
        return cfg

    # -------------------------
    # Public API
    # -------------------------
    def acquire(self, tokens: int = 1) -> AcquireResult:
        """
        Attempt to acquire tokens (default 1).
        If denied, returns retry_after_seconds.
        """
        tokens = int(tokens)
        if tokens <= 0:
            return AcquireResult(allowed=True, retry_after_seconds=0)

        now = self._now()
        limit, interval, jitter_max = self._load_config()

        window_start = self._window_start(now, interval)
        window_end = window_start + interval
        counter_key = self._counter_key(window_start)

        # TTL slightly larger than interval so old window keys expire
        ttl_seconds = max(interval * 2, 5)

        try:
            allowed = self.redis.eval(
                self._lua,
                numkeys=1,
                keys=[counter_key],
                args=[str(tokens), str(ttl_seconds), str(limit)],
            )
        except Exception:
            if self.deny_on_redis_error:
                # safest for protecting downstream (Mongo/API)
                retry_after = int(max(1.0, float(interval)))
                return AcquireResult(allowed=False, retry_after_seconds=retry_after)
            return AcquireResult(allowed=True, retry_after_seconds=0)

        if allowed == 1:
            return AcquireResult(allowed=True, retry_after_seconds=0)

        # Denied: retry after next window + jitter to avoid waves
        base = max(0.0, window_end - now)
        jitter = random.uniform(0.0, float(jitter_max))
        retry_after = int(max(1.0, base + jitter))

        return AcquireResult(allowed=False, retry_after_seconds=retry_after)
