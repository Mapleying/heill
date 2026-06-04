"""Exchange rate tool — exchangerate-api.com (free, no key), in-process cache 1h."""
import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[float, dict]] = {}  # {base: (timestamp, rates_dict)}
_CACHE_TTL = 3600

_FALLBACKS = {
    ("EUR", "GBP"): 0.86, ("GBP", "EUR"): 1.16,
    ("USD", "GBP"): 0.79, ("GBP", "USD"): 1.27,
    ("EUR", "USD"): 1.08, ("USD", "EUR"): 0.93,
}


async def run(tool_input: dict[str, Any]) -> dict:
    from_cur: str = tool_input["from_currency"].upper()
    to_cur: str = tool_input["to_currency"].upper()

    if from_cur == to_cur:
        return {"from": from_cur, "to": to_cur, "rate": 1.0, "from_cache": True}

    cached = _cache.get(from_cur)
    try:
        if cached and (time.time() - cached[0]) < _CACHE_TTL:
            rates = cached[1]
            from_cache = True
        else:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"https://api.exchangerate-api.com/v4/latest/{from_cur}")
                resp.raise_for_status()
                rates = resp.json()["rates"]
                _cache[from_cur] = (time.time(), rates)
            from_cache = False

        rate = rates.get(to_cur)
        if rate is None:
            return {"error": f"Unknown currency: {to_cur}"}

        return {"from": from_cur, "to": to_cur, "rate": rate, "from_cache": from_cache}

    except Exception as exc:
        logger.warning("Exchange rate fetch failed: %s", exc)
        fallback = _FALLBACKS.get((from_cur, to_cur))
        if fallback:
            return {"from": from_cur, "to": to_cur, "rate": fallback, "from_cache": False, "warning": "Using fallback rate"}
        return {"error": str(exc)}
