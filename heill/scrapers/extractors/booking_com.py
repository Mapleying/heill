"""Booking.com HTML parser — extracts hotel listings from search results page."""
import re

from bs4 import BeautifulSoup


def parse_listings(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    results = []

    cards = (
        soup.find_all("div", {"data-testid": "property-card"})
        or soup.find_all("div", class_=re.compile(r"sr_item|property_name|hotel_name", re.I))
        or soup.find_all("article")
    )

    for card in cards[:10]:
        try:
            name_el = card.find(attrs={"data-testid": "title"}) or card.find(
                class_=re.compile(r"fcab3ed991|title|name", re.I)
            )
            price_el = card.find(attrs={"data-testid": "price-and-discounted-price"}) or card.find(
                class_=re.compile(r"prco-valign|price|rate", re.I)
            )
            score_el = card.find(attrs={"data-testid": "review-score"}) or card.find(
                class_=re.compile(r"b5cd09854e|score|rating", re.I)
            )

            name = name_el.get_text(strip=True) if name_el else ""
            if not name:
                continue

            price_text = price_el.get_text(strip=True) if price_el else ""
            price_match = re.search(r"[\£\$\€]?\s*(\d[\d,]+)", price_text)
            price = float(price_match.group(1).replace(",", "")) if price_match else None

            link_el = card.find("a", href=True)
            url = link_el["href"] if link_el else None
            if url and not url.startswith("http"):
                url = f"https://www.booking.com{url}"

            results.append({
                "name": name,
                "price_per_night": price,
                "currency": "EUR",
                "url": url,
                "score": score_el.get_text(strip=True) if score_el else None,
            })
        except Exception:
            continue

    return results
