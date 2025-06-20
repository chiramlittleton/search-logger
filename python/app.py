from fastapi import FastAPI, Request
from pydantic import BaseModel
from logger import log_search

app = FastAPI()

class SearchPayload(BaseModel):
    keyword: str
    user_id: str | None = None
    session_id: str

@app.post("/log")
async def log_endpoint(payload: SearchPayload, request: Request):
    await log_search(payload.keyword, payload.user_id, payload.session_id)
    return {"status": "ok"}
