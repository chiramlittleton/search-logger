import redis.asyncio as aioredis
import asyncpg
from datetime import datetime, timedelta, timezone

class Logger:
    def __init__(self, redis_url, db_config, debounce_seconds=5):
        self.redis_url = redis_url
        self.db_config = db_config
        self.redis = None
        self.pg_pool = None
        self.debounce_buffer = timedelta(seconds=debounce_seconds)

    async def init(self):
        self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
        self.pg_pool = await asyncpg.create_pool(**self.db_config)

    async def log(self, keyword: str, session_id: str, user_id: str = None):
        """
        Called by the API handler for each progressive search input.
        Stores only the longest keyword within a short time window using Redis.
        """
        key = f"search:{session_id}"
        current = await self.redis.get(key)

        # Only overwrite if this keyword is longer (more complete)
        if not current or len(keyword) > len(current):
            await self.redis.set(key, keyword, ex=10)
            await self.redis.set(f"{key}:ts", datetime.now(timezone.utc).isoformat(), ex=10)
            if user_id:
                await self.redis.set(f"{key}:user", user_id, ex=10)

    async def acquire_pg_conn(self):
        return await self.pg_pool.acquire()

    async def flush(self):
        """
        Periodically flushes the most complete keywords from Redis into Postgres.
        Called from a background task.
        Only flushes if a buffer time has passed since last update.
        """
        now = datetime.now(timezone.utc)
        keys = await self.redis.keys("search:*")
        search_keys = [k for k in keys if not (k.endswith(":user") or k.endswith(":ts"))]

        for key in search_keys:
            keyword = await self.redis.get(key)
            session_id = key.split("search:")[1]
            user_key = f"{key}:user"
            ts_key = f"{key}:ts"

            user_id = await self.redis.get(user_key)
            created_at_str = await self.redis.get(ts_key)

            if not created_at_str:
                continue

            try:
                created_at = datetime.fromisoformat(created_at_str)
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

            # Skip if the debounce buffer hasn't passed yet
            if now - created_at < self.debounce_buffer:
                continue

            async with await self.acquire_pg_conn() as conn:
                await conn.execute(
                    """
                    INSERT INTO search_logs (keyword, session_id, user_id, created_at)
                    VALUES ($1, $2, $3, $4)
                    """,
                    keyword,
                    session_id,
                    user_id,
                    created_at
                )

            # Clean up Redis keys
            await self.redis.delete(key, user_key, ts_key)

    async def close(self):
        await self.pg_pool.close()
        await self.redis.close()
