"""
search_flights tool — Google Flights via Playwright.
Falls back to indicative stub data when Playwright is unavailable.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def run(tool_input: dict[str, Any]) -> dict:
    origin: str = tool_input["origin"]
    destination: str = tool_input["destination"]
    outbound_date: str = tool_input["outbound_date"]
    return_date: str = tool_input.get("return_date", "")
    adults: int = tool_input.get("adults", 1)
    currency: str = tool_input.get("currency", "GBP")

    try:
        results = await _scrape_google_flights(origin, destination, outbound_date, return_date)
        if results:
            return {"flights": results, "currency": currency, "origin": origin, "destination": destination}
    except Exception as exc:
        logger.warning("Google Flights scrape failed: %s", exc)

    return _stub(origin, destination, outbound_date, return_date, currency)


async def _scrape_google_flights(
    origin: str, destination: str, outbound_date: str, return_date: str
) -> list[dict]:
    from heill.scrapers.browser_pool import fetch_with_browser
    from heill.scrapers.extractors.google_flights import parse_flights

    url = (
        f"https://www.google.com/travel/flights"
        f"?q=Flights+from+{origin}+to+{destination}&hl=en&curr=GBP"
    )
    html = await fetch_with_browser(url, wait_for="networkidle")
    return parse_flights(html)


def _stub(
    origin: str, destination: str, outbound_date: str, return_date: str, currency: str
) -> dict:
    return {
        "flights": [
            {
                "airline": "easyJet",
                "origin": origin,
                "destination": destination,
                "outbound_date": outbound_date,
                "return_date": return_date,
                "price": 189,
                "currency": currency,
                "note": "INDICATIVE_ONLY",
            },
            {
                "airline": "Ryanair",
                "origin": origin,
                "destination": destination,
                "outbound_date": outbound_date,
                "return_date": return_date,
                "price": 145,
                "currency": currency,
                "note": "INDICATIVE_ONLY",
            },
            {
                "airline": "British Airways",
                "origin": origin,
                "destination": destination,
                "outbound_date": outbound_date,
                "return_date": return_date,
                "price": 310,
                "currency": currency,
                "note": "INDICATIVE_ONLY",
            },
        ],
        "currency": currency,
        "origin": origin,
        "destination": destination,
        "source": "stub_fallback",
        "warning": "Flight prices are illustrative — verify on Google Flights or Skyscanner before booking.",
    }
