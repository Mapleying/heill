from __future__ import annotations

from pydantic import BaseModel


class Money(BaseModel):
    amount: float
    currency: str


class FlightOption(BaseModel):
    airline: str
    origin: str
    destination: str
    outbound_date: str
    return_date: str | None = None
    price: Money
    deep_link: str | None = None
    duration_minutes: int | None = None


class AccommodationOption(BaseModel):
    name: str
    location: str
    stars: int | None = None
    price_per_night: Money
    total_price: Money | None = None
    url: str | None = None
    distance_from_venue: str | None = None


class ActivityOption(BaseModel):
    provider_name: str
    sport: str
    dates: str | None = None
    duration_days: int | None = None
    skill_levels: list[str] = []
    price_per_person: Money
    accommodation_included: bool = False
    url: str | None = None


class ItineraryOption(BaseModel):
    id: str
    label: str
    total_cost: Money
    flight: FlightOption | None = None
    accommodation: AccommodationOption | None = None
    activity: ActivityOption
    rationale: str
    sources: list[str] = []


class RecommendationOutput(BaseModel):
    itineraries: list[ItineraryOption]
    caveats: list[str] = []
    follow_up_questions: list[str] = []
