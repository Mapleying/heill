"""
browse_page tool.
Tier 1: httpx + BS4 (static pages, ~2-5s).
Tier 2: Playwright (JS-rendered pages, ~8-20s, optional).
"""
import logging
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from heill.scrapers.extractors.generic import extract_text, extract_title, is_js_rendered
from heill.scrapers.extractors.structured import extract_structured

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}


async def run(tool_input: dict[str, Any]) -> dict:
    url: str = tool_input["url"]
    extract_mode: str = tool_input.get("extract_mode", "text")
    max_chars: int = tool_input.get("max_chars", 8000)

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return {"error": f"Invalid URL scheme: {parsed.scheme}", "url": url}

    start = time.monotonic()
    html, tier = await _fetch(url)
    title = extract_title(html)

    if extract_mode == "structured":
        content = extract_text(html, max_chars=4000)
        result = {
            "url": url,
            "title": title,
            "content": content,
            "structured": extract_structured(html),
            "tier": tier,
            "elapsed_ms": int((time.monotonic() - start) * 1000),
        }
    else:
        result = {
            "url": url,
            "title": title,
            "content": extract_text(html, max_chars=max_chars),
            "tier": tier,
            "elapsed_ms": int((time.monotonic() - start) * 1000),
        }

    return result


async def _fetch(url: str) -> tuple[str, str]:
    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text

        if is_js_rendered(html):
            logger.debug("JS-rendered: %s — trying Playwright", url)
            pw_html = await _try_playwright(url)
            if pw_html:
                return pw_html, "playwright"

        return html, "httpx"

    except Exception as exc:
        logger.warning("httpx fetch failed for %s: %s", url, exc)
        pw_html = await _try_playwright(url)
        if pw_html:
            return pw_html, "playwright"
        return f"<html><body>Fetch failed: {exc}</body></html>", "error"


async def _try_playwright(url: str) -> str | None:
    try:
        from heill.scrapers.browser_pool import fetch_with_browser
        return await fetch_with_browser(url)
    except RuntimeError:
        return None
    except Exception as exc:
        logger.warning("Playwright fetch failed for %s: %s", url, exc)
        return None
