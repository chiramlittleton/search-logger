import pytest
from unittest.mock import AsyncMock, patch
from logger import Logger
from datetime import datetime, timedelta, timezone


def make_awaitable(result):
    class Awaitable:
        def __await__(self):
            yield
            return result
    return Awaitable()


def make_pg_context_manager(pg_conn):
    cm = AsyncMock()
    cm.__aenter__.return_value = pg_conn
    return cm


@pytest.mark.asyncio
@patch("logger.Logger.acquire_pg_conn")
@patch("logger.asyncpg.create_pool")
@patch("logger.aioredis.from_url")
async def test_deduplicates_and_logs_final_term(mock_from_url, mock_create_pool, mock_acquire_conn):
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.keys = AsyncMock(return_value=["search:abc"])
    mock_redis.delete = AsyncMock()

    ts = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    mock_redis.get.side_effect = lambda key: {
        "search:abc": "Business",
        "search:abc:ts": ts,
        "search:abc:user": "u1"
    }.get(key)

    pg_conn = AsyncMock()
    pg_conn.execute = AsyncMock()
    mock_acquire_conn.return_value = make_pg_context_manager(pg_conn)

    mock_from_url.return_value = make_awaitable(mock_redis)
    mock_create_pool.return_value = make_awaitable(AsyncMock())

    logger = Logger("redis://fake", db_config={})
    await logger.init()

    await logger.log("B", "abc", "u1")
    await logger.log("Bu", "abc", "u1")
    await logger.log("Bus", "abc", "u1")
    await logger.log("Busin", "abc", "u1")
    await logger.log("Business", "abc", "u1")

    await logger.flush()

    pg_conn.execute.assert_called_once()
    args = pg_conn.execute.call_args[0]
    assert args[1] == "Business"
    assert args[2] == "abc"
    assert args[3] == "u1"


@pytest.mark.asyncio
@patch("logger.Logger.acquire_pg_conn")
@patch("logger.asyncpg.create_pool")
@patch("logger.aioredis.from_url")
async def test_flush_skips_if_buffer_not_elapsed(mock_from_url, mock_create_pool, mock_acquire_conn):
    mock_redis = AsyncMock()
    recent = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    mock_redis.get.side_effect = lambda k: {
        "search:abc": "Business",
        "search:abc:ts": recent,
        "search:abc:user": "u1"
    }.get(k)
    mock_redis.keys = AsyncMock(return_value=["search:abc"])
    mock_redis.delete = AsyncMock()

    pg_conn = AsyncMock()
    pg_conn.execute = AsyncMock()
    mock_acquire_conn.return_value = make_pg_context_manager(pg_conn)

    mock_from_url.return_value = make_awaitable(mock_redis)
    mock_create_pool.return_value = make_awaitable(AsyncMock())

    logger = Logger("redis://", {}, debounce_seconds=5)
    await logger.init()
    await logger.flush()

    pg_conn.execute.assert_not_called()


@pytest.mark.asyncio
@patch("logger.Logger.acquire_pg_conn")
@patch("logger.asyncpg.create_pool")
@patch("logger.aioredis.from_url")
async def test_flush_skips_invalid_timestamp(mock_from_url, mock_create_pool, mock_acquire_conn):
    mock_redis = AsyncMock()
    mock_redis.get.side_effect = lambda k: {
        "search:abc": "hello",
        "search:abc:ts": "INVALID_TIMESTAMP",
        "search:abc:user": "u1"
    }.get(k)
    mock_redis.keys = AsyncMock(return_value=["search:abc"])
    mock_redis.delete = AsyncMock()

    pg_conn = AsyncMock()
    pg_conn.execute = AsyncMock()
    mock_acquire_conn.return_value = make_pg_context_manager(pg_conn)

    mock_from_url.return_value = make_awaitable(mock_redis)
    mock_create_pool.return_value = make_awaitable(AsyncMock())

    logger = Logger("redis://", {}, debounce_seconds=1)
    await logger.init()
    await logger.flush()

    pg_conn.execute.assert_not_called()


@pytest.mark.asyncio
@patch("logger.Logger.acquire_pg_conn")
@patch("logger.asyncpg.create_pool")
@patch("logger.aioredis.from_url")
async def test_flush_handles_missing_user(mock_from_url, mock_create_pool, mock_acquire_conn):
    ts = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    mock_redis = AsyncMock()
    mock_redis.get.side_effect = lambda k: {
        "search:abc": "hello",
        "search:abc:ts": ts,
        "search:abc:user": None
    }.get(k)
    mock_redis.keys = AsyncMock(return_value=["search:abc"])
    mock_redis.delete = AsyncMock()

    pg_conn = AsyncMock()
    pg_conn.execute = AsyncMock()
    mock_acquire_conn.return_value = make_pg_context_manager(pg_conn)

    mock_from_url.return_value = make_awaitable(mock_redis)
    mock_create_pool.return_value = make_awaitable(AsyncMock())

    logger = Logger("redis://", {}, debounce_seconds=1)
    await logger.init()
    await logger.flush()

    pg_conn.execute.assert_called_once()
    args = pg_conn.execute.call_args[0]
    assert args[1] == "hello"
    assert args[2] == "abc"
    assert args[3] is None

@pytest.mark.asyncio
@patch("logger.Logger.acquire_pg_conn")
@patch("logger.asyncpg.create_pool")
@patch("logger.aioredis.from_url")
async def test_same_keyword_different_sessions(mock_from_url, mock_create_pool, mock_acquire_conn):
    ts = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()

    mock_redis = AsyncMock()
    mock_redis.keys = AsyncMock(return_value=["search:sessionA", "search:sessionB"])
    mock_redis.get.side_effect = lambda k: {
        "search:sessionA": "Business",
        "search:sessionA:ts": ts,
        "search:sessionA:user": "userA",
        "search:sessionB": "Business",
        "search:sessionB:ts": ts,
        "search:sessionB:user": "userB"
    }.get(k)
    mock_redis.delete = AsyncMock()

    pg_conn = AsyncMock()
    pg_conn.execute = AsyncMock()
    cm = AsyncMock()
    cm.__aenter__.return_value = pg_conn

    mock_from_url.return_value = make_awaitable(mock_redis)
    mock_create_pool.return_value = make_awaitable(AsyncMock())
    mock_acquire_conn.return_value = cm

    logger = Logger("redis://", {}, debounce_seconds=1)
    await logger.init()
    await logger.flush()

    assert pg_conn.execute.call_count == 2
    calls = [call.args for call in pg_conn.execute.call_args_list]
    assert ("Business", "sessionA", "userA") in [(c[1], c[2], c[3]) for c in calls]
    assert ("Business", "sessionB", "userB") in [(c[1], c[2], c[3]) for c in calls]
