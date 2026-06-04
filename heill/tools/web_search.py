"""Web search — SerpAPI if configured, DuckDuckGo otherwise."""
import asyncio
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")


async def run(tool_input: dict[str, Any]) -> dict:
    query: str = tool_input["query"]
    num_results: int = tool_input.get("num_results", 5)

    if SERPAPI_KEY:
        return await _serpapi(query, num_results)
    return await _duckduckgo(query, num_results)


async def _serpapi(query: str, num: int) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://serpapi.com/search",
            params={"q": query, "num": num, "api_key": SERPAPI_KEY, "engine": "google"},
        )
        resp.raise_for_status()
        data = resp.json()
        results = [
            {"title": r.get("title", ""), "url": r.get("link", ""), "snippet": r.get("snippet", "")}
            for r in data.get("organic_results", [])[:num]
        ]
        return {"results": results, "query": query}


async def _duckduckgo(query: str, num: int) -> dict:
    try:
        from duckduckgo_search import DDGS

        def _sync():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=num))

        raw = await asyncio.to_thread(_sync)
        results = [
            {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
            for r in raw
        ]
        return {"results": results, "query": query}
    except Exception as exc:
        logger.warning("DuckDuckGo search failed: %s", exc)
        return {"results": [], "query": query, "error": str(exc)}
