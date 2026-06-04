"""Tool dispatch registry and OpenAI-compatible function schemas."""
import logging
from typing import Any, Callable

from heill.tools.accommodation import run as accommodation_run
from heill.tools.browse_page import run as browse_page_run
from heill.tools.exchange_rate import run as exchange_rate_run
from heill.tools.flights import run as flights_run
from heill.tools.sport_activities import run as sport_activities_run
from heill.tools.web_search import run as web_search_run

logger = logging.getLogger(__name__)

TOOL_REGISTRY: dict[str, Callable] = {
    "web_search": web_search_run,
    "browse_page": browse_page_run,
    "search_flights": flights_run,
    "search_accommodation": accommodation_run,
    "find_sport_activities": sport_activities_run,
    "get_exchange_rate": exchange_rate_run,
}

# OpenAI function-calling format
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for sports camps, venues, travel options, or any topic. Returns titles, URLs, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "num_results": {"type": "integer", "description": "Number of results (default 5)", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browse_page",
            "description": "Fetch and extract content from a specific URL. Use to get details about a sports camp or check a provider's prices.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to browse"},
                    "extract_mode": {
                        "type": "string",
                        "enum": ["text", "structured"],
                        "description": "'text' for plain content, 'structured' to extract prices/dates/skill levels",
                    },
                    "max_chars": {"type": "integer", "description": "Maximum characters to return (default 8000)"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Search for flights between two cities on specific dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Origin city or airport code (e.g. 'London' or 'LHR')"},
                    "destination": {"type": "string", "description": "Destination city or airport code"},
                    "outbound_date": {"type": "string", "description": "Outbound date YYYY-MM-DD"},
                    "return_date": {"type": "string", "description": "Return date YYYY-MM-DD"},
                    "adults": {"type": "integer", "description": "Number of adult passengers"},
                    "currency": {"type": "string", "description": "Currency code e.g. 'GBP'"},
                },
                "required": ["origin", "destination", "outbound_date", "return_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_accommodation",
            "description": "Search for hotels and accommodation at a destination.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Location, city, or region"},
                    "checkin_date": {"type": "string", "description": "Check-in date YYYY-MM-DD"},
                    "checkout_date": {"type": "string", "description": "Check-out date YYYY-MM-DD"},
                    "adults": {"type": "integer", "description": "Number of adults"},
                    "max_price_per_night": {"type": "number", "description": "Maximum price per night"},
                },
                "required": ["location", "checkin_date", "checkout_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_sport_activities",
            "description": (
                "PRIMARY TOOL. Find sports activity holidays, camps, retreats, and clinics. "
                "Use this first for any sports travel query. Searches specialist aggregators and the web "
                "to surface providers that standard travel sites don't cover."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sport": {"type": "string", "description": "The sport e.g. 'tennis', 'surf', 'golf', 'ski', 'football'"},
                    "location": {"type": "string", "description": "Location or region e.g. 'Spain', 'Portugal', 'Mallorca'"},
                    "month": {"type": "string", "description": "Month and year e.g. 'August 2025'"},
                    "activity_type": {
                        "type": "string",
                        "enum": ["camp", "clinic", "retreat", "tour", "any"],
                    },
                    "skill_level": {
                        "type": "string",
                        "enum": ["beginner", "intermediate", "advanced", "any"],
                    },
                    "max_price": {"type": "number", "description": "Maximum price per person"},
                },
                "required": ["sport", "location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "Get the current exchange rate between two currencies to convert prices.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_currency": {"type": "string", "description": "Source currency code e.g. 'EUR'"},
                    "to_currency": {"type": "string", "description": "Target currency code e.g. 'GBP'"},
                },
                "required": ["from_currency", "to_currency"],
            },
        },
    },
]


async def dispatch_tool(name: str, tool_input: dict[str, Any]) -> dict:
    handler = TOOL_REGISTRY.get(name)
    if not handler:
        return {"error": f"Unknown tool: {name}"}
    try:
        return await handler(tool_input)
    except Exception as exc:
        logger.exception("Tool %s raised: %s", name, exc)
        return {"error": str(exc), "tool": name}
