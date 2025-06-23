import asyncio
from logger import Logger

# Instantiate the logger with Redis and Postgres config
logger = Logger(
    redis_url="redis://redis:6379/0",
    db_config={
        "user": "search",
        "password": "search",
        "database": "search_logs",
        "host": "postgres",
        "port": 5432,
    },
    debounce_seconds=5  # Adjust this as needed
)

async def main():
    await logger.init()

    try:
        while True:
            await logger.flush()
            await asyncio.sleep(1)  # Check every second
    finally:
        await logger.close()

if __name__ == "__main__":
    asyncio.run(main())
