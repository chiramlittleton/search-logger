import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from logger import Logger
from datetime import datetime, timedelta

@pytest.fixture
def mock_redis():
    r = MagicMock()
    r.set = AsyncMock()
    r.get = AsyncMock()
    r.ttl = AsyncMock()
    r.keys = AsyncMock()
    r.delete = AsyncMock()
    return r

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    return db

@pytest.mark.asyncio
async def test_save_search_sets_redis_key(mock_redis, mock_db):
    logger = Logger(redis=mock_redis, db_conn=mock_db)
    await logger.save_search("sess123", "user456", "python")

    mock_redis.set.assert_awaited_with("search:sess123", "python", ex=3)

@pytest.mark.asyncio
async def test_flush_flushes_keys(mock_redis, mock_db):
    logger = Logger(redis=mock_redis, db_conn=mock_db)

    mock_redis.keys.return_value = ["search:sess123"]
    mock_redis.ttl.return_value = 0.5
    mock_redis.get.return_value = "python"

    await logger.flush()

    mock_db.execute.assert_awaited()
    mock_redis.delete.assert_awaited_with("search:sess123")
