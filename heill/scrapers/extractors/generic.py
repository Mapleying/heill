import re

from bs4 import BeautifulSoup

_NOISE_TAGS = {"script", "style", "nav", "footer", "header", "aside", "noscript", "iframe", "svg"}


def extract_text(html: str, max_chars: int = 8000) -> str:
    """Extract clean readable text from HTML."""
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    for tag in soup(_NOISE_TAGS):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def extract_title(html: str) -> str:
    try:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("title")
        return title.get_text(strip=True) if title else ""
    except Exception:
        return ""


def is_js_rendered(html: str) -> bool:
    """Heuristic: True if the page body is too sparse to be useful without JS."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        body = soup.find("body")
        if not body:
            return True
        text = body.get_text(strip=True)
        script_count = len(soup.find_all("script"))
        return len(text) < 200 and script_count > 3
    except Exception:
        return False
