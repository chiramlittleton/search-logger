import pytest
import asyncio
from unittest.mock import AsyncMock, ANY
from datetime import datetime, timedelta, timezone

from logger import Logger


@pytest.mark.asyncio
async def test_flush_deduplicates_and_inserts():
    mock_redis = AsyncMock()
    mock_pg_pool = AsyncMock()
    mock_conn = AsyncMock()

    # ✅ Patch both acquire and release
    mock_pg_pool.acquire = AsyncMock(return_value=mock_conn)
    mock_pg_pool.release = AsyncMock()

    session_id = "abc123"
    keyword = "python"
    user_id = "user456"

    ts = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()

    mock_redis.keys.return_value = [f"search:{session_id}"]
    mock_redis.get.side_effect = lambda k: {
        f"search:{session_id}": keyword,
        f"search:{session_id}:ts": ts,
        f"search:{session_id}:user": user_id,
    }.get(k)

    logger = Logger(redis_url="unused", db_config={}, debounce_seconds=10)
    logger.redis = mock_redis
    logger.pg_pool = mock_pg_pool

    await logger.flush()

    mock_conn.execute.assert_awaited_once_with(
        ANY,
        keyword,
        session_id,
        user_id,
        ANY  # <- Ignore exact datetime matching
    )

    mock_redis.delete.assert_awaited_with(
        f"search:{session_id}",
        f"search:{session_id}:user",
        f"search:{session_id}:ts"
    )


@pytest.mark.asyncio
async def test_flush_skips_if_debounce_not_elapsed():
    mock_redis = AsyncMock()
    mock_pg_pool = AsyncMock()

    session_id = "debounce1"
    keyword = "ai"
    user_id = "u1"

    # Too recent, should trigger debounce skip
    ts = datetime.now(timezone.utc).isoformat()

    mock_redis.keys.return_value = [f"search:{session_id}"]
    mock_redis.get.side_effect = lambda k: {
        f"search:{session_id}": keyword,
        f"search:{session_id}:ts": ts,
        f"search:{session_id}:user": user_id,
    }.get(k)

    logger = Logger(redis_url="unused", db_config={}, debounce_seconds=60)
    logger.redis = mock_redis
    logger.pg_pool = mock_pg_pool

    await logger.flush()

    assert not mock_pg_pool.acquire.called


@pytest.mark.asyncio
async def test_flush_skips_if_timestamp_missing():
    mock_redis = AsyncMock()
    mock_pg_pool = AsyncMock()

    session_id = "notimestamp"
    keyword = "cloud"

    mock_redis.keys.return_value = [f"search:{session_id}"]
    mock_redis.get.side_effect = lambda k: {
        f"search:{session_id}": keyword,
        f"search:{session_id}:ts": None,
        f"search:{session_id}:user": None,
    }.get(k)

    logger = Logger(redis_url="unused", db_config={})
    logger.redis = mock_redis
    logger.pg_pool = mock_pg_pool

    await logger.flush()

    assert not mock_pg_pool.acquire.called
    assert not mock_redis.delete.called
