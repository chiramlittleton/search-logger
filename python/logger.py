import asyncpg

# Config matches what's in docker-compose for postgres
DB_CONFIG = {
    "user": "search",
    "password": "search",
    "database": "search_logs",
    "host": "postgres",  # this is the docker-compose service name
    "port": 5432
}

async def log_search(keyword: str, user_id: str | None, session_id: str):
    conn = await asyncpg.connect(**DB_CONFIG)

    await conn.execute("""
        INSERT INTO search_logs (user_id, session_id, keyword)
        VALUES ($1, $2, $3)
    """, user_id, session_id, keyword)

    await conn.close()
