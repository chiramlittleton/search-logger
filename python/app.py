from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from logger import Logger

app = FastAPI()

# Initialize the logger with Redis and Postgres config
logger = Logger(
    redis_url="redis://redis:6379/0",
    db_config={
        "user": "search",
        "password": "search",
        "database": "search_logs",
        "host": "postgres",
        "port": 5432,
    },
    debounce_seconds=5  # Only log the most complete search within 5s per session
)

@app.on_event("startup")
async def startup():
    await logger.init()  # Connect to Redis and DB pools

@app.on_event("shutdown")
async def shutdown():
    await logger.close()  # Clean up connections

class SearchLogRequest(BaseModel):
    keyword: str
    session_id: str  # Unique per anonymous user session or logged-in session
    user_id: Optional[str] = None  # Present if the user is logged in

@app.post("/log")
async def handle_log_search(payload: SearchLogRequest):
    await logger.log(
        keyword=payload.keyword,
        session_id=payload.session_id,
        user_id=payload.user_id
    )
    return {"status": "ok"}
