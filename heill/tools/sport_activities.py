"""
find_sport_activities — three-level discovery funnel.
Level 1: sports_registry.yaml curated aggregators.
Level 2: web_search + browse top results.
Level 3: empty list (LLM falls back to trained knowledge in the conversation).
"""
import asyncio
import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
import yaml
from bs4 import BeautifulSoup

from heill.scrapers.extractors.generic import extract_text
from heill.scrapers.extractors.structured import extract_structured
from heill.tools.web_search import run as web_search

logger = logging.getLogger(__name__)

_REGISTRY_PATH = Path(__file__).parent.parent / "scrapers" / "sports_registry.yaml"
_registry: dict | None = None

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

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


def _load_registry() -> dict:
    global _registry
    if _registry is None:
        with _REGISTRY_PATH.open() as f:
            _registry = yaml.safe_load(f) or {}
    return _registry


async def run(tool_input: dict[str, Any]) -> dict:
    sport: str = tool_input["sport"].lower().strip()
    sport = _SPORT_ALIASES.get(sport, sport)
    location: str = tool_input["location"]
    month: str | None = tool_input.get("month")
    skill_level: str = tool_input.get("skill_level", "any")
    max_price: float | None = tool_input.get("max_price")

    registry = _load_registry()
    sport_config = registry.get(sport)
    activities: list[dict] = []

    # Level 1: Registry aggregators
    if sport_config and sport_config.get("aggregators"):
        tasks = [_scrape_aggregator(agg, location) for agg in sport_config["aggregators"]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, list):
                activities.extend(r)

    # Level 2: Search fallback when registry has nothing useful
    if len(activities) < 2:
        search_terms = (sport_config or {}).get("search_terms", [f"{sport} camp"])
        query = f"{search_terms[0]} {location}"
        if month:
            query += f" {month}"

        search_resp = await web_search({"query": query, "num_results": 5})
        urls = [r["url"] for r in search_resp.get("results", [])[:3]]

        browse_tasks = [_browse_for_activities(url, sport) for url in urls]
        browse_results = await asyncio.gather(*browse_tasks, return_exceptions=True)
        for r in browse_results:
            if isinstance(r, list):
                activities.extend(r)

    # Deduplicate by URL
    seen: set[str] = set()
    unique: list[dict] = []
    for act in activities:
        key = act.get("url", act.get("title", ""))
        if key not in seen:
            seen.add(key)
            unique.append(act)

    # Filter
    if skill_level != "any":
        unique = [
            a for a in unique
            if not a.get("skill_levels") or skill_level in " ".join(a.get("skill_levels", []))
        ]
    if max_price:
        unique = [a for a in unique if not a.get("price_per_person") or a["price_per_person"] <= max_price]

    return {
        "sport": sport,
        "location": location,
        "month": month,
        "activities": unique[:8],
        "total_found": len(unique),
    }


async def _scrape_aggregator(agg_config: dict, location: str) -> list[dict]:
    url = agg_config.get("url", "")
    selectors = agg_config.get("selectors", {})
    provider_name = agg_config.get("name", "Unknown")
    if not url:
        return []

    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
    except Exception as exc:
        logger.warning("Failed to scrape %s: %s", url, exc)
        return []

    return _parse_page(resp.text, url, provider_name, selectors)


def _parse_page(html: str, base_url: str, provider_name: str, selectors: dict) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    activities: list[dict] = []

    container_sel = selectors.get("container", "article, .card, .listing")
    try:
        containers = soup.select(container_sel)
    except Exception:
        containers = []

    if len(containers) < 2:
        # Fallback: return full-page text extraction as a single entry
        text = extract_text(html, max_chars=5000)
        structured = extract_structured(html)
        if text and len(text) > 100:
            activities.append({
                "provider_name": provider_name,
                "url": base_url,
                "raw_text": text[:600],
                "prices_found": structured.get("prices", []),
                "dates_found": structured.get("dates", []),
                "skill_levels": structured.get("skill_levels", []),
                "source": "aggregator_text",
            })
        return activities

    for container in containers[:6]:
        try:
            t_sel = selectors.get("title", "h2, h3, h4")
            p_sel = selectors.get("price", ".price, [class*='price']")
            d_sel = selectors.get("dates", ".dates, [class*='date']")
            l_sel = selectors.get("location", ".location")

            title_el = container.select_one(t_sel)
            price_el = container.select_one(p_sel)
            date_el = container.select_one(d_sel)
            loc_el = container.select_one(l_sel)
            link_el = container.find("a", href=True)

            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            price_text = price_el.get_text(strip=True) if price_el else ""
            pm = re.search(r"[\£\$\€]?\s*(\d[\d,]*)", price_text)
            price = float(pm.group(1).replace(",", "")) if pm else None

            href = link_el["href"] if link_el else ""
            if href and not href.startswith("http"):
                href = urljoin(base_url, href)

            activities.append({
                "provider_name": provider_name,
                "title": title,
                "url": href or base_url,
                "price_per_person": price,
                "currency": "GBP",
                "dates": date_el.get_text(strip=True) if date_el else None,
                "location_hint": loc_el.get_text(strip=True) if loc_el else None,
                "source": "aggregator_selector",
            })
        except Exception:
            continue

    return activities


async def _browse_for_activities(url: str, sport: str) -> list[dict]:
    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        html = resp.text
    except Exception as exc:
        logger.warning("Browse failed for %s: %s", url, exc)
        return []

    text = extract_text(html, max_chars=4000)
    if len(text) < 100:
        return []

    structured = extract_structured(html)
    title = ""
    try:
        soup = BeautifulSoup(html, "html.parser")
        t = soup.find("title")
        title = t.get_text(strip=True) if t else ""
    except Exception:
        pass

    return [{
        "provider_name": title or url,
        "url": url,
        "sport": sport,
        "raw_text": text[:600],
        "prices_found": structured.get("prices", []),
        "dates_found": structured.get("dates", []),
        "skill_levels": structured.get("skill_levels", []),
        "source": "search_browse",
    }]
