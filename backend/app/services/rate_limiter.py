"""
Rate limiting service.
Provides a simple rate limiter with Redis support and an in-memory fallback.
"""

import time
import asyncio
from typing import Dict, List, Optional, Any

try:
    import redis.asyncio as redis
except ImportError:
    try:
        import redis
    except ImportError:
        redis = None

from fastapi import HTTPException, status, Request

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Simple rate limiter with Redis support and an in-memory fallback.
    """

    def __init__(self):
        self._redis = None
        self._redis_enabled = False
        self._in_memory: Dict[str, List[float]] = {}
        self._last_cleanup = time.time()

        if settings.redis_url and redis:
            try:
                # Use Redis from_url - handles both sync and async depending on which redis was imported
                self._redis = redis.from_url(settings.redis_url, decode_responses=True)
                self._redis_enabled = True
                logger.info("Configured Redis for rate limiting")
            except Exception as e:
                logger.error(
                    "Failed to configure Redis for rate limiting. Falling back to in-memory storage.",
                    error=str(e)
                )
                self._redis = None
        elif settings.redis_url and not redis:
            logger.warning("Redis URL configured but 'redis' package not installed. Using in-memory rate limiting.")
        else:
            logger.info("Redis URL not configured. Using in-memory rate limiting.")

    async def _cleanup_in_memory(self, now: float):
        """
        Remove keys that have no recent timestamps to prevent memory leaks.
        """
        keys_to_delete = []
        for key, timestamps in self._in_memory.items():
            # If the newest timestamp is older than 1 hour, the key is probably stale
            # We use a generous window for cleanup
            if not timestamps or timestamps[-1] < now - 3600:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self._in_memory[key]

        if keys_to_delete:
            logger.debug("Cleaned up stale rate limit keys", count=len(keys_to_delete))

    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """
        Check if a request is allowed under the rate limit.

        Args:
            key: Unique key for the rate limit (e.g., IP address, user ID)
            limit: Maximum number of requests allowed in the window
            window: Time window in seconds

        Returns:
            True if allowed, False otherwise
        """
        # Try Redis first if enabled
        if self._redis_enabled and self._redis:
            try:
                current_time = int(time.time())
                window_key = f"rate_limit:{key}:{current_time // window}"

                # Use a pipeline to ensure atomic increment and expire (mitigates race condition)
                # Note: incr and expire in a pipeline is still two commands, but better
                # Using a Lua script would be truly atomic but more complex to implement here
                async with self._redis.pipeline(transaction=True) as pipe:
                    pipe.incr(window_key)
                    pipe.expire(window_key, window)
                    results = await pipe.execute()
                    count = results[0]

                return count <= limit
            except Exception as e:
                logger.error("Error with Redis rate limiting", error=str(e), key=key)
                # Fallback to in-memory for this request

        # In-memory fallback (sliding window)
        now = time.time()

        # Periodic cleanup (every 10 minutes or if memory seems high)
        if now - self._last_cleanup > 600:
            await self._cleanup_in_memory(now)
            self._last_cleanup = now

        if key not in self._in_memory:
            self._in_memory[key] = []

        # Filter out timestamps outside the current window
        self._in_memory[key] = [ts for ts in self._in_memory[key] if ts > now - window]

        if len(self._in_memory[key]) >= limit:
            return False

        # Add current timestamp
        self._in_memory[key].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


async def login_rate_limit(request: Request):
    """
    Dependency for login rate limiting.
    Limits requests based on client IP address.
    """
    ip_address = request.client.host if request.client else "unknown"
    key = f"login:{ip_address}"

    is_allowed = await rate_limiter.is_allowed(
        key=key,
        limit=settings.login_rate_limit_count,
        window=settings.login_rate_limit_window
    )

    if not is_allowed:
        logger.warning(
            "Rate limit exceeded for login",
            ip_address=ip_address,
            limit=settings.login_rate_limit_count,
            window=settings.login_rate_limit_window
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
