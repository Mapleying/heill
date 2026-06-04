from __future__ import annotations

import time

from pydantic import BaseModel, Field


class TripContext(BaseModel):
    sport: str | None = None
    destination_region: str | None = None
    travel_dates: dict | None = None  # {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
    budget: dict | None = None  # {"amount": 2000, "currency": "GBP"}
    party_size: int | None = None
    skill_level: str | None = None
    departure_city: str | None = None


class SessionData(BaseModel):
    session_id: str
    messages: list[dict] = Field(default_factory=list)
    trip_context: TripContext = Field(default_factory=TripContext)
    scrape_cache: dict = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
