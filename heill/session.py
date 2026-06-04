import logging
import uuid
from datetime import datetime, timedelta, timezone

from supabase import AsyncClient

logger = logging.getLogger(__name__)

SESSION_TTL = 7200  # 2-hour sliding TTL

_TABLE = "sessions"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expires() -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=SESSION_TTL)).isoformat()


def _new(session_id: str | None = None) -> dict:
    now = _now()
    return {
        "session_id": session_id or str(uuid.uuid4()),
        "messages": [],
        "trip_context": {
            "sport": None,
            "destination_region": None,
            "travel_dates": None,
            "budget": None,
            "party_size": None,
            "skill_level": None,
            "departure_city": None,
        },
        "scrape_cache": {},
        "created_at": now,
        "updated_at": now,
        "expires_at": _expires(),
    }


async def load_or_create(session_id: str | None, supabase: AsyncClient) -> dict:
    if session_id:
        resp = await (
            supabase.table(_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .gt("expires_at", _now())
            .execute()
        )
        if resp.data:
            session = resp.data[0]
            # Slide TTL
            await (
                supabase.table(_TABLE)
                .update({"expires_at": _expires(), "updated_at": _now()})
                .eq("session_id", session_id)
                .execute()
            )
            return session

    session = _new(session_id)
    await supabase.table(_TABLE).insert(session).execute()
    return session


async def save(session: dict, supabase: AsyncClient) -> None:
    session["updated_at"] = _now()
    session["expires_at"] = _expires()
    await supabase.table(_TABLE).upsert(session).execute()


async def get(session_id: str, supabase: AsyncClient) -> dict | None:
    resp = await (
        supabase.table(_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .gt("expires_at", _now())
        .execute()
    )
    return resp.data[0] if resp.data else None


async def delete(session_id: str, supabase: AsyncClient) -> bool:
    resp = await supabase.table(_TABLE).delete().eq("session_id", session_id).execute()
    return bool(resp.data)
