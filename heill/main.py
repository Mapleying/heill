"""
Heill API — FastAPI app.

Endpoints:
  POST /chat          → SSE stream (session_id?, message)
  GET  /sessions/{id} → session JSON
  DELETE /sessions/{id}
  GET  /health
"""
import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from supabase import AsyncClient, create_async_client

from heill import agent, session
from heill.scrapers.browser_pool import start_pool, stop_pool

structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.INFO))
logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Supabase singleton
# ---------------------------------------------------------------------------
_supabase: AsyncClient | None = None


def get_supabase() -> AsyncClient:
    assert _supabase is not None, "Supabase not initialised"
    return _supabase


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _supabase
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    _supabase = await create_async_client(url, key)
    logger.info("Supabase connected", url=url)

    await start_pool()

    yield

    await stop_pool()
    logger.info("Shutdown complete")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Heill", version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
@limiter.limit("10/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    supabase: AsyncClient = Depends(get_supabase),
):
    sess = await session.load_or_create(body.session_id, supabase)
    sess["messages"].append({"role": "user", "content": body.message})

    async def generate():
        yield f"data: {json.dumps({'type': 'session_id', 'session_id': sess['session_id']})}\n\n"

        async for chunk in agent.run_agent(sess, supabase):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/sessions/{session_id}")
async def get_session(session_id: str, supabase: AsyncClient = Depends(get_supabase)):
    sess = await session.get(session_id, supabase)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return sess


@app.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str, supabase: AsyncClient = Depends(get_supabase)):
    deleted = await session.delete(session_id, supabase)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
