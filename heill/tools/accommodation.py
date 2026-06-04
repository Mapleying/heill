"""
search_accommodation tool — Booking.com via httpx + BS4.
Falls back to indicative stub data when scraping fails.
"""
import logging
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}


async def run(tool_input: dict[str, Any]) -> dict:
    location: str = tool_input["location"]
    checkin: str = tool_input["checkin_date"]
    checkout: str = tool_input["checkout_date"]
    adults: int = tool_input.get("adults", 1)
    max_price: float | None = tool_input.get("max_price_per_night")

    try:
        results = await _scrape_booking(location, checkin, checkout, adults)
        if results:
            if max_price:
                results = [r for r in results if not r.get("price_per_night") or r["price_per_night"] <= max_price]
            return {"accommodation": results[:5], "location": location, "checkin": checkin, "checkout": checkout}
    except Exception as exc:
        logger.warning("Booking.com scrape failed: %s", exc)

    return _stub(location, checkin, checkout)


async def _scrape_booking(location: str, checkin: str, checkout: str, adults: int) -> list[dict]:
    from heill.scrapers.extractors.booking_com import parse_listings

    ci = checkin.split("-")
    co = checkout.split("-")
    url = (
        f"https://www.booking.com/searchresults.en-gb.html"
        f"?ss={quote(location)}"
        f"&checkin_year={ci[0]}&checkin_month={ci[1]}&checkin_monthday={ci[2]}"
        f"&checkout_year={co[0]}&checkout_month={co[1]}&checkout_monthday={co[2]}"
        f"&group_adults={adults}&no_rooms=1"
    )
    async with httpx.AsyncClient(headers=_HEADERS, timeout=20, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return parse_listings(resp.text)


def _stub(location: str, checkin: str, checkout: str) -> dict:
    return {
        "accommodation": [
            {
                "name": f"Hotel Central {location}",
                "location": location,
                "price_per_night": 65,
                "currency": "EUR",
                "stars": 3,
                "url": "https://www.booking.com",
                "note": "INDICATIVE_ONLY",
            },
            {
                "name": f"Boutique Aparthotel {location}",
                "location": location,
                "price_per_night": 95,
                "currency": "EUR",
                "stars": 4,
                "url": "https://www.booking.com",
                "note": "INDICATIVE_ONLY",
            },
        ],
        "location": location,
        "checkin": checkin,
        "checkout": checkout,
        "source": "stub_fallback",
        "warning": "Accommodation prices are illustrative — verify on Booking.com before booking.",
    }
