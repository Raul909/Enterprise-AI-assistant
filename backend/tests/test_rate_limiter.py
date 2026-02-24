import sys
import os
import asyncio
import time
from unittest.mock import MagicMock, patch, AsyncMock
from types import ModuleType

# Mock necessary modules that are missing in the environment
def mock_module(name):
    m = ModuleType(name)
    sys.modules[name] = m
    return m

mock_modules = [
    "fastapi", "redis", "redis.asyncio", "structlog", "structlog.types",
    "jose", "passlib", "passlib.context", "sqlalchemy",
    "sqlalchemy.ext.asyncio", "sqlalchemy.orm", "pydantic",
    "pydantic_settings", "core", "core.config", "core.logging"
]

for module_name in mock_modules:
    try:
        if module_name not in sys.modules:
            mock_module(module_name)
    except ImportError:
        mock_module(module_name)

# Additional setup for specific mocks
if "fastapi" in sys.modules:
    m = sys.modules["fastapi"]
    if not hasattr(m, "HTTPException"):
        m.HTTPException = type("HTTPException", (Exception,), {"status_code": 0})
        def __init_http_exception__(self, status_code, detail=None, headers=None):
            self.status_code = status_code
            self.detail = detail
            self.headers = headers
        m.HTTPException.__init__ = __init_http_exception__
    m.status = MagicMock()
    m.status.HTTP_429_TOO_MANY_REQUESTS = 429
    m.Depends = MagicMock()
    m.Request = MagicMock()
    m.APIRouter = MagicMock()

if "core.config" in sys.modules:
    m = sys.modules["core.config"]
    m.settings = MagicMock()
    m.settings.redis_url = None
    m.settings.login_rate_limit_count = 2
    m.settings.login_rate_limit_window = 1

if "core.logging" in sys.modules:
    m = sys.modules["core.logging"]
    m.get_logger = MagicMock()

if "structlog" in sys.modules:
    m = sys.modules["structlog"]
    m.get_logger = MagicMock()

# Add backend/app to path
backend_app_path = os.path.join(os.getcwd(), "backend/app")
if backend_app_path not in sys.path:
    sys.path.append(backend_app_path)

# Now we can import our service
try:
    import services.rate_limiter as rate_limiter_module
    PATCH_TARGET = "services.rate_limiter"
except ImportError:
    # Try direct import
    services_path = os.path.join(backend_app_path, "services")
    if services_path not in sys.path:
        sys.path.append(services_path)
    import rate_limiter as rate_limiter_module
    PATCH_TARGET = "rate_limiter"

RateLimiter = rate_limiter_module.RateLimiter
login_rate_limit = rate_limiter_module.login_rate_limit

def test_rate_limiter_in_memory():
    """Test the in-memory rate limiting logic."""
    async def run_test():
        with patch(f"{PATCH_TARGET}.settings") as mock_settings:
            mock_settings.redis_url = None
            limiter = RateLimiter()

            key = "test_key"
            limit = 2
            window = 1

            # First request - allowed
            assert await limiter.is_allowed(key, limit, window) is True
            # Second request - allowed
            assert await limiter.is_allowed(key, limit, window) is True
            # Third request - blocked
            assert await limiter.is_allowed(key, limit, window) is False

            # Wait for window to expire
            await asyncio.sleep(1.1)

            # Should be allowed again
            assert await limiter.is_allowed(key, limit, window) is True
    asyncio.run(run_test())

def test_rate_limiter_redis():
    """Test the Redis-backed rate limiting logic."""
    async def run_test():
        mock_redis_lib = MagicMock()
        with patch(f"{PATCH_TARGET}.redis", mock_redis_lib):
            mock_redis_conn = AsyncMock()
            mock_redis_lib.from_url.return_value = mock_redis_conn

            # pipeline() is a sync call returning an async context manager
            mock_redis_conn.pipeline = MagicMock()
            mock_pipeline = MagicMock()
            mock_pipeline.execute = AsyncMock()
            # Correctly mock async context manager
            mock_redis_conn.pipeline.return_value.__aenter__ = AsyncMock(return_value=mock_pipeline)
            mock_redis_conn.pipeline.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch(f"{PATCH_TARGET}.settings") as mock_settings:
                mock_settings.redis_url = "redis://localhost"

                limiter = RateLimiter()
                # Force enable redis for testing
                limiter._redis_enabled = True
                limiter._redis = mock_redis_conn

                key = "test_key_redis"
                limit = 2
                window = 60

                # Mock pipeline execute results
                mock_pipeline.execute.side_effect = [[1, True], [2, True], [3, True]]

                # First request - allowed
                assert await limiter.is_allowed(key, limit, window) is True
                mock_pipeline.incr.assert_called()
                mock_pipeline.expire.assert_called()

                # Second request - allowed
                assert await limiter.is_allowed(key, limit, window) is True

                # Third request - blocked
                assert await limiter.is_allowed(key, limit, window) is False
    asyncio.run(run_test())

def test_login_rate_limit_dependency():
    """Test the FastAPI dependency function."""
    async def run_test():
        mock_request = MagicMock()
        mock_request.client.host = "1.2.3.4"

        with patch(f"{PATCH_TARGET}.rate_limiter", new_callable=AsyncMock) as mock_limiter:
            with patch(f"{PATCH_TARGET}.settings") as mock_settings:
                mock_settings.login_rate_limit_count = 5
                mock_settings.login_rate_limit_window = 60

                # Case 1: Allowed
                mock_limiter.is_allowed.return_value = True
                await login_rate_limit(mock_request)
                mock_limiter.is_allowed.assert_called_with(
                    key="login:1.2.3.4",
                    limit=5,
                    window=60
                )

                # Case 2: Blocked
                mock_limiter.is_allowed.return_value = False
                from fastapi import HTTPException
                try:
                    await login_rate_limit(mock_request)
                    assert False, "Should have raised HTTPException"
                except HTTPException as e:
                    assert e.status_code == 429
    asyncio.run(run_test())
