from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from logger import Logger

app = FastAPI()

# Logger instance with debounce configuration
logger = Logger(
    redis_url="redis://redis:6379/0",
    db_config={
        "user": "search",
        "password": "search",
        "database": "search_logs",
        "host": "postgres",
        "port": 5432,
    },
    debounce_seconds=5  # ⏱ Adjust this window to tune dedup behavior
)

@app.on_event("startup")
async def startup():
    await logger.init()

@app.on_event("shutdown")
async def shutdown():
    await logger.close()

class SearchLogRequest(BaseModel):
    keyword: str
    session_id: str
    user_id: Optional[str] = None

@app.post("/log")
async def handle_log_search(payload: SearchLogRequest):
    await logger.log(
        keyword=payload.keyword,
        session_id=payload.session_id,
        user_id=payload.user_id
    )
    return {"status": "ok"}
