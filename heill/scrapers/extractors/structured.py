import re

_PRICE_PATTERNS = [
    r"£\s*(\d[\d,]*(?:\.\d{2})?)",
    r"\$\s*(\d[\d,]*(?:\.\d{2})?)",
    r"€\s*(\d[\d,]*(?:\.\d{2})?)",
    r"(\d[\d,]*(?:\.\d{2})?)\s*(?:GBP|USD|EUR)",
    r"from\s*(?:£|\$|€)\s*(\d[\d,]*)",
    r"(?:per person|pp)\s*:?\s*(?:£|\$|€)?\s*(\d[\d,]*)",
]

_DATE_PATTERNS = [
    r"\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})\b",
    r"\b((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:\s*[-–]\s*\d{1,2})?,?\s*\d{4})\b",
    r"\b(\d{4}-\d{2}-\d{2})\b",
]

_SKILL_KEYWORDS = ["beginner", "intermediate", "advanced", "all levels", "all abilities", "open level"]


def extract_structured(html: str) -> dict:
    """Extract prices, dates, and skill levels from page text."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(" ", strip=True)
    except Exception:
        text = html

    prices: list[float] = []
    for pattern in _PRICE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            raw = match.group(1).replace(",", "")
            try:
                val = float(raw)
                if 10 < val < 50000:  # sanity range
                    prices.append(val)
            except ValueError:
                pass

    dates: list[str] = []
    for pattern in _DATE_PATTERNS:
        dates.extend(re.findall(pattern, text, re.IGNORECASE))

    levels = [kw for kw in _SKILL_KEYWORDS if kw.lower() in text.lower()]

    return {
        "prices": sorted(set(prices)),
        "dates": list(dict.fromkeys(dates))[:10],
        "skill_levels": levels,
    }
