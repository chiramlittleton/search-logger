import redis.asyncio as aioredis
import asyncpg
from datetime import datetime, timedelta, timezone
import pytz  # ensure this is installed

class Logger:
    def __init__(self, redis_url, db_config, debounce_seconds=5):
        self.redis_url = redis_url
        self.db_config = db_config
        self.redis = None
        self.pg_pool = None
        self.debounce_buffer = timedelta(seconds=debounce_seconds)

    async def init(self):
        print("🔌 Initializing Redis and Postgres connections...")
        self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
        self.pg_pool = await asyncpg.create_pool(**self.db_config)
        print("✅ Redis and Postgres initialized")

    async def log(self, keyword: str, session_id: str, user_id: str = None):
        key = f"search:{session_id}"
        print(f"📝 Logging keyword='{keyword}' for session='{session_id}' user='{user_id}'")

        current = await self.redis.get(key)
        print(f"🔍 Current Redis value for {key} = {current}")

        if not current or len(keyword) > len(current):
            await self.redis.set(key, keyword, ex=10)
            await self.redis.set(f"{key}:ts", datetime.now(timezone.utc).isoformat(), ex=10)
            print(f"💾 Set {key} = {keyword}, and timestamp")

            if user_id:
                await self.redis.set(f"{key}:user", user_id, ex=10)
                print(f"👤 Set {key}:user = {user_id}")

    async def acquire_pg_conn(self):
        print("📥 Acquiring Postgres connection...")
        return await self.pg_pool.acquire()

    async def flush(self):
        print("🧼 Starting flush...")
        now = datetime.now(timezone.utc)
        keys = await self.redis.keys("search:*")
        print(f"🔑 Redis keys found: {keys}")

        search_keys = [k for k in keys if not (k.endswith(":user") or k.endswith(":ts"))]
        print(f"🗂 Search keys to process: {search_keys}")

        flush_count = 0

        for key in search_keys:
            keyword = await self.redis.get(key)
            session_id = key.split("search:")[1]
            user_key = f"{key}:user"
            ts_key = f"{key}:ts"

            user_id = await self.redis.get(user_key)
            created_at_str = await self.redis.get(ts_key)

            print(f"📦 Entry: keyword={keyword}, session_id={session_id}, user_id={user_id}, ts={created_at_str}")

            if not created_at_str:
                print("⚠️ Skipping due to missing timestamp")
                continue

            try:
                created_at = datetime.fromisoformat(created_at_str)
            except ValueError:
                print("❌ Invalid timestamp format:", created_at_str)
                continue

            if created_at.tzinfo is None or created_at.tzinfo.utcoffset(created_at) is None:
                print("⚠️ Naive datetime detected, replacing tzinfo=timezone.utc")
                created_at = created_at.replace(tzinfo=timezone.utc)
            else:
                created_at = created_at.astimezone(timezone.utc)

            print(f"🧮 Now={now}, Created={created_at}, Elapsed={(now - created_at).total_seconds()}s")

            if now - created_at < self.debounce_buffer:
                print(f"⏱ Skipping due to debounce buffer ({(now - created_at).total_seconds()}s elapsed)")
                continue

            print("📨 Writing to Postgres...")
            conn = await self.acquire_pg_conn()
            try:
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
                flush_count += 1
                print(f"✅ Inserted: {keyword}, {session_id}, {user_id}, {created_at}")
            finally:
                await self.pg_pool.release(conn)

            await self.redis.delete(key, user_key, ts_key)
            print(f"🧹 Deleted Redis keys: {key}, {user_key}, {ts_key}")

        print(f"📊 Total flushed entries: {flush_count}")

    async def close(self):
        print("🔒 Closing connections...")
        await self.pg_pool.close()
        await self.redis.close()
        print("✅ Connections closed")
