"""
find_sport_activities — looks up the curated sportscation catalogue.
Edit heill/data/sportscations.yaml to add or update available packages.
"""
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_CATALOGUE_PATH = Path(__file__).parent.parent / "data" / "sportscations.yaml"
_catalogue: list[dict] | None = None

_SPORT_ALIASES = {
    "surfing": "surf",
    "soccer": "football",
    "snowboarding": "ski",
    "snowboard": "ski",
    "padel tennis": "padel",
    "mountain bike": "cycling",
    "mtb": "cycling",
    "road cycling": "cycling",
}


def _load_catalogue() -> list[dict]:
    global _catalogue
    if _catalogue is None:
        with _CATALOGUE_PATH.open() as f:
            _catalogue = yaml.safe_load(f) or []
    return _catalogue


def _matches_location(entry: dict, location: str) -> bool:
    location_lower = location.lower()
    searchable = " ".join([
        entry.get("location", ""),
        entry.get("country", ""),
        entry.get("region", ""),
        " ".join(entry.get("tags", [])),
    ]).lower()
    return any(word in searchable for word in location_lower.split())


def _matches_month(entry: dict, month: str) -> bool:
    if not entry.get("dates"):
        return True
    month_lower = month.lower()
    return any(month_lower in d.lower() for d in entry["dates"])


def _matches_skill(entry: dict, skill_level: str) -> bool:
    if skill_level == "any":
        return True
    levels = [s.lower() for s in entry.get("skill_levels", [])]
    return not levels or "all" in levels or skill_level in levels


async def run(tool_input: dict[str, Any]) -> dict:
    sport: str = tool_input["sport"].lower().strip()
    sport = _SPORT_ALIASES.get(sport, sport)
    location: str = tool_input["location"]
    month: str | None = tool_input.get("month")
    activity_type: str = tool_input.get("activity_type", "any")
    skill_level: str = tool_input.get("skill_level", "any")
    max_price: float | None = tool_input.get("max_price")

    catalogue = _load_catalogue()
    results: list[dict] = []

    for entry in catalogue:
        if entry.get("sport", "").lower() != sport:
            continue
        if not _matches_location(entry, location):
            continue
        if month and not _matches_month(entry, month):
            continue
        if activity_type != "any" and entry.get("activity_type", "any") not in ("any", activity_type):
            continue
        if not _matches_skill(entry, skill_level):
            continue
        if max_price and entry.get("price_per_person") and entry["price_per_person"] > max_price:
            continue
        results.append(entry)

    activities = [
        {
            "provider_name": e.get("provider_name", ""),
            "title": e.get("title", ""),
            "url": e.get("url", ""),
            "location": e.get("location", ""),
            "activity_type": e.get("activity_type", ""),
            "skill_levels": e.get("skill_levels", []),
            "duration_days": e.get("duration_days"),
            "price_per_person": e.get("price_per_person"),
            "currency": e.get("currency", "GBP"),
            "includes_accommodation": e.get("includes_accommodation", False),
            "dates": e.get("dates", []),
            "description": e.get("description", ""),
            "source": "catalogue",
        }
        for e in results
    ]

    return {
        "sport": sport,
        "location": location,
        "month": month,
        "activities": activities,
        "total_found": len(activities),
    }
