"""Google Flights HTML parser — expects rendered HTML from Playwright."""
import re

from bs4 import BeautifulSoup


def parse_flights(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    results = []

    # Google Flights uses dynamic class names; target structural patterns
    flight_rows = (
        soup.find_all("li", attrs={"class": re.compile(r"pIav2d", re.I)})
        or soup.find_all("div", attrs={"role": "listitem"})
        or []
    )

    for row in flight_rows[:8]:
        try:
            price_el = row.find(class_=re.compile(r"YMlIz|price|fare|cost", re.I))
            airline_el = row.find(class_=re.compile(r"h1fkLb|airline|carrier|Zz0bId", re.I))
            time_els = row.find_all(class_=re.compile(r"wtdjmc|time|ADdCu", re.I))

            price_text = price_el.get_text(strip=True) if price_el else ""
            price_match = re.search(r"[\£\$\€]?(\d[\d,]+)", price_text)
            price = float(price_match.group(1).replace(",", "")) if price_match else None

            if not price:
                continue

            airline = airline_el.get_text(strip=True) if airline_el else "Unknown"
            times = [t.get_text(strip=True) for t in time_els[:2]]

            results.append({
                "airline": airline,
                "price": price,
                "currency": "GBP",
                "departure_time": times[0] if times else None,
                "arrival_time": times[1] if len(times) > 1 else None,
            })
        except Exception:
            continue

    return results
