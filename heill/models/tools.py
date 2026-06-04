from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class WebSearchInput(BaseModel):
    query: str = Field(description="The search query")
    num_results: int = Field(default=5, description="Number of results to return")


class BrowsePageInput(BaseModel):
    url: str = Field(description="The URL to browse")
    extract_mode: Literal["text", "structured"] = Field(default="text")
    max_chars: int = Field(default=8000)


class SearchFlightsInput(BaseModel):
    origin: str = Field(description="Origin city or airport code")
    destination: str = Field(description="Destination city or airport code")
    outbound_date: str = Field(description="Outbound date YYYY-MM-DD")
    return_date: str = Field(description="Return date YYYY-MM-DD")
    adults: int = Field(default=1)
    currency: str = Field(default="GBP")


class SearchAccommodationInput(BaseModel):
    location: str = Field(description="Location to search")
    checkin_date: str = Field(description="Check-in date YYYY-MM-DD")
    checkout_date: str = Field(description="Check-out date YYYY-MM-DD")
    adults: int = Field(default=1)
    max_price_per_night: float | None = Field(default=None)


class FindSportActivitiesInput(BaseModel):
    sport: str = Field(description="The sport")
    location: str = Field(description="Location or region")
    month: str | None = Field(default=None, description="Month and year e.g. 'August 2025'")
    activity_type: Literal["camp", "clinic", "retreat", "tour", "any"] = Field(default="any")
    skill_level: Literal["beginner", "intermediate", "advanced", "any"] = Field(default="any")
    max_price: float | None = Field(default=None)


class GetExchangeRateInput(BaseModel):
    from_currency: str = Field(description="Source currency code e.g. 'EUR'")
    to_currency: str = Field(description="Target currency code e.g. 'GBP'")
