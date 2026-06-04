# Heill — System Specification: AI-Powered Sports Travel Agent

## Context

Heill is a greenfield AI travel agent specialised in sports activity holidays (tennis camps,
surf retreats, football tours, golf breaks, ski trips, and any other sport). The system enables
users to plan complete sports travel packages — flights, accommodation, and the activity itself —
through a natural-language chat interface. The agent browses live websites at query time to
surface specialist providers (e.g. Rafa Nadal Academy, surfholidays.com) that standard travel
APIs do not index.

---

## 1. High-Level Architecture

```
┌────────────────────────────────────────────────────────────┐
│  CHAT UI  (Next.js 14 + Tailwind + custom SSE hook)        │
│  Streams SSE, renders itinerary cards                       │
└────────────────────────┬───────────────────────────────────┘
                         │ HTTPS / SSE
┌────────────────────────▼───────────────────────────────────┐
│  API GATEWAY  (FastAPI, Python 3.12)                        │
│  POST /chat → SSE stream  |  GET/DELETE /sessions/{id}      │
└────────────┬────────────────────────────┬──────────────────┘
             │                            │
    ┌────────▼────────┐        ┌──────────▼──────────────────┐
    │  Supabase       │        │  AI ORCHESTRATION           │
    │  (PostgreSQL)   │        │  agent.py (custom loop)     │
    │  - messages     │        │  Claude claude-sonnet-4-6   │
    │  - trip_context │        │  + tool_use                 │
    │  - scrape cache │        │  + prompt caching           │
    │  TTL: expires_at│        └──────────┬──────────────────┘
    └─────────────────┘                   │ dispatches tools
                               ┌──────────▼──────────────────┐
                               │  TOOL REGISTRY              │
                               │  web_search | browse_page   │
                               │  search_flights             │
                               │  search_accommodation       │
                               │  find_sport_activities      │
                               │  get_exchange_rate          │
                               └──────────┬──────────────────┘
                                          │
                               ┌──────────▼──────────────────┐
                               │  BROWSER / SCRAPE TIER      │
                               │  httpx + BS4 (Tier 1)       │
                               │  Playwright pool x3 (Tier 2)│
                               │                             │
                               │  Targets: Google Flights,   │
                               │  Booking.com, Skyscanner,   │
                               │  sport-specific aggregators │
                               └─────────────────────────────┘
```

---

## 2. Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| LLM | `claude-sonnet-4-6` | Best tool-use accuracy; prompt caching cuts cost on long sessions |
| Backend | FastAPI (Python 3.12) | Async-native, SSE streaming built-in, Pydantic validation |
| Agent loop | Custom `heill/agent.py` (~150 lines) | Full control over streaming, caching, tool dispatch — no LangChain overhead |
| Browser automation | Playwright (async, pool of 3) | JS-rendered SPA support; async pool cuts wall-clock time |
| Lightweight scraping | httpx + BeautifulSoup 4 | Async, handles malformed HTML, fast for static pages |
| Session store | Supabase (PostgreSQL) | Managed Postgres, JSONB columns for messages/context/cache, `expires_at` column for sliding TTL, no self-hosted infrastructure |
| Frontend | Next.js 14 + Vercel AI SDK | `useChat` hook handles SSE out of the box |

---

## 3. Agent Design

### System Prompt Summary
Claude is briefed as "Heill, a specialist AI travel agent for sports activity holidays." It:
- Extracts sport, destination, dates, budget, party size, skill level from conversation
- Asks one clarifying question per turn until minimum fields are present
- Uses tools to research activities, flights, and accommodation
- Never fabricates prices; always cites source URLs
- Returns a structured `json` block + conversational summary when research is complete

### Agentic Loop State Machine
```
USER_MESSAGE → BUILD_PROMPT → CALL_CLAUDE (streaming)
                                    │
                      tool_use ─────┤
                                    │
                   DISPATCH_TOOLS (asyncio.gather for concurrent tools)
                                    │
                   INJECT_TOOL_RESULTS → back to BUILD_PROMPT
                                    │
                      end_turn ─────┘
                                    │
                   STREAM_FINAL_RESPONSE → SAVE_SESSION
```

### Prompt Caching
Apply `cache_control: {"type": "ephemeral"}` on the system prompt and conversation history
blocks to reduce latency and cost on multi-turn planning sessions.

---

## 4. Tools

### `web_search`
Search Google/Bing for camps, venues, or any unknown URL.
- Input: `query` (string), `num_results` (int, default 5)
- Output: list of `{title, url, snippet}`
- Implementation: SerpAPI (recommended) or DuckDuckGo (no key)

### `browse_page`
Fetch and extract content from a URL. Two-tier:
- Tier 1: httpx + BS4 (static pages, ~2-5s)
- Tier 2: Playwright (JS-rendered pages, ~8-20s)
- Input: `url`, `extract_mode` (text|structured), `max_chars` (default 8000)
- Output: `{url, title, content, structured: {prices, dates, levels}, from_cache}`

### `search_flights`
Scrape Google Flights (Playwright), fallback Skyscanner.
- Input: `origin`, `destination`, `outbound_date`, `return_date`, `adults`, `currency`
- Output: list of flight options with airline, times, price, deep_link
- Cache TTL: 30 minutes

### `search_accommodation`
Scrape Booking.com (httpx + BS4).
- Input: `location`, `checkin_date`, `checkout_date`, `adults`, `max_price_per_night`
- Output: list of accommodation options with price, stars, distance, URL
- Cache TTL: 1 hour
- Skip if activity already includes accommodation

### `find_sport_activities` ← primary differentiator
Three-level discovery funnel:
1. **Registry** (`sports_registry.yaml`): sport → curated aggregator URLs + CSS selectors
2. **Search fallback**: `web_search("{sport} camp {location} {month} {year}")`, spider top 2-3 results
3. **LLM-assisted** (last resort): Claude names likely providers from training knowledge; agent verifies by browsing

- Input: `sport`, `location`, `month`, `activity_type` (camp|clinic|retreat|tour|any), `skill_level`, `max_price`
- Output: normalised activity objects `{provider_name, sport, dates, duration_days, skill_levels, price_per_person, accommodation_included, url}`
- Cache TTL: 24 hours

### `get_exchange_rate`
Convert prices to user's currency. Uses exchangerate-api.com (free, cached 1 hour).

---

## 5. Data Flow — Sample Query

**Query**: "Tennis camp in Spain, August, budget £2000, flying from London, intermediate player"

```
Turn 1: All fields present → agent fires tools immediately

  find_sport_activities(sport=tennis, location=Spain, month=Aug 2025, skill_level=intermediate)
    → Registry: tenniscompete.com, rafanadalacademy.com
    → Returns 6 normalised activity objects

  search_flights(origin=London, destination=Palma, dates=Aug 1-15)
    → Google Flights via Playwright
    → Returns 5 options; cheapest easyJet £189 return

  search_accommodation(location=Manacor Mallorca, checkin=Aug 4, checkout=Aug 11)
    → Booking.com; cheapest €55/night
    → (Some camps include accommodation → agent detects and skips)

  get_exchange_rate(EUR → GBP)
    → 0.86

Turn 2: Claude synthesises → 2-3 itinerary options in JSON + conversational summary

Frontend renders itinerary cards. Total elapsed: ~25-40s.
```

---

## 6. Session Data Model (Supabase, TTL 2h sliding)

Sessions are stored in a single `sessions` table in Supabase (PostgreSQL). The `messages`, `trip_context`, and `scrape_cache` columns are `JSONB`. TTL is implemented via an `expires_at` `TIMESTAMPTZ` column refreshed on every read/write; a pg_cron job or scheduled function cleans up expired rows.

**Table schema** (`supabase/migrations/001_sessions.sql`):

| Column | Type | Notes |
|---|---|---|
| `session_id` | `TEXT` (PK) | UUID v4 generated in Python |
| `messages` | `JSONB` | Anthropic API message history |
| `trip_context` | `JSONB` | Extracted trip fields |
| `scrape_cache` | `JSONB` | Per-session scrape result cache |
| `created_at` | `TIMESTAMPTZ` | Immutable, set on insert |
| `updated_at` | `TIMESTAMPTZ` | Refreshed on every save |
| `expires_at` | `TIMESTAMPTZ` | Sliding 2h window; rows with `expires_at < NOW()` are treated as gone |

**Row shape** (as Python dict):

```json
{
  "session_id": "uuid-v4",
  "messages": [...],
  "trip_context": {
    "sport": "tennis",
    "destination_region": "Spain",
    "travel_dates": {"start": "2025-08-01", "end": "2025-08-15"},
    "budget": {"amount": 2000, "currency": "GBP"},
    "party_size": 1,
    "skill_level": "intermediate",
    "departure_city": "London"
  },
  "scrape_cache": {
    "camps:tennis:spain:august2025": {"ttl": 86400},
    "flights:LHR:PMI:20250801:20250815": {"ttl": 1800}
  },
  "created_at": "2025-08-01T14:00:00+00:00",
  "updated_at": "2025-08-01T14:22:00+00:00",
  "expires_at": "2025-08-01T16:22:00+00:00"
}
```

---

## 7. Recommendation Output Schema

```json
{
  "itineraries": [
    {
      "id": "option_1",
      "label": "Best value",
      "total_cost": {"amount": 1589, "currency": "GBP"},
      "flight": {},
      "accommodation": {},
      "activity": {},
      "rationale": "Stays within budget with £411 spare for meals...",
      "sources": ["url1", "url2"]
    }
  ],
  "caveats": ["Prices scraped at 14:22 UTC; verify before booking"],
  "follow_up_questions": ["Single or shared room at the academy?"]
}
```

---

## 8. Non-Functional Requirements

| Concern | Requirement |
|---|---|
| Latency (no-tool turn) | P50 < 2s, P95 < 4s |
| Latency (full search, uncached) | P50 < 35s, P95 < 60s |
| Frontend feedback | Progressive status updates ("Searching camps... Found 6. Now checking flights...") |
| Scraping failures | Return partial results; Claude instructs user to verify missing data manually; never fabricate |
| Rate limiting | 10 req/min per IP via `slowapi`; per-domain scrape throttling in `scrapers/config.yaml` |
| Security | URL allowlist before Playwright opens any link (prevent SSRF); UUID4 session IDs; no PII beyond session TTL |
| Observability | Structured JSON logs per tool call (tool, duration_ms, from_cache, error); Sentry; Prometheus metrics |
| Browser pool | 3 concurrent Playwright instances (~200 MB RAM each); health-checked every 30s |

---

## 9. Project Structure

```
heill/
├── Dockerfile
├── docker-compose.yml          # API service only (no Redis)
├── pyproject.toml
├── supabase/
│   └── migrations/
│       └── 001_sessions.sql    # sessions table DDL
│
├── heill/
│   ├── main.py                     # FastAPI app, /chat SSE, /sessions routes
│   ├── agent.py                    # Agentic loop — CRITICAL FILE
│   ├── session.py                  # Supabase session CRUD, trip_context extraction
│   ├── prompts.py                  # System prompt + synthesis prompt templates
│   │
│   ├── tools/
│   │   ├── registry.py             # Tool dispatch + Claude-facing JSON schemas
│   │   ├── web_search.py
│   │   ├── browse_page.py
│   │   ├── flights.py
│   │   ├── accommodation.py
│   │   ├── sport_activities.py     # Three-level discovery funnel — CRITICAL FILE
│   │   └── exchange_rate.py
│   │
│   ├── scrapers/
│   │   ├── browser_pool.py         # Playwright async pool — CRITICAL FILE
│   │   ├── config.yaml             # Per-domain rate limits, UA rotation
│   │   ├── sports_registry.yaml    # Sport → aggregator URLs + selectors — CRITICAL FILE
│   │   └── extractors/
│   │       ├── booking_com.py
│   │       ├── google_flights.py
│   │       ├── generic.py
│   │       └── structured.py
│   │
│   └── models/
│       ├── session.py
│       ├── tools.py
│       └── itinerary.py
│
├── frontend/
│   └── app/
│       └── chat/
│           ├── page.tsx
│           └── components/
│               ├── MessageBubble.tsx
│               ├── ItineraryCard.tsx
│               ├── ToolStatusBanner.tsx
│               └── ChatInput.tsx
│
└── tests/
    ├── unit/
    ├── integration/
    ├── e2e/
    └── fixtures/scraping/          # Recorded HTML for offline tests
```

---

## 10. Implementation Sequence (5 Sprints)

| Sprint | Goal | Deliverable |
|---|---|---|
| 1 | Skeleton | FastAPI SSE + Supabase sessions + Next.js chat UI + Claude multi-turn (no tools) |
| 2 | Core tools | `web_search`, `browse_page` (httpx only), `find_sport_activities` (registry, 3-4 sports) |
| 3 | Flights + hotels | Playwright pool, `search_flights`, `search_accommodation`, Supabase scrape cache |
| 4 | Synthesis + UI | Itinerary JSON synthesis, card rendering, `get_exchange_rate`, error handling |
| 5 | Robustness | LLM-assisted discovery fallback, prompt caching, integration tests, Sentry + metrics |

---

## 11. Verification

**Unit tests** (`pytest + respx + unittest.mock`):
- Each tool with recorded HTML fixtures
- Agent loop: clarification flow, tool injection, max-depth guard

**Integration tests** (`pytest-recording` VCR):
- Live scrapes for 10 common sport/location combos
- Run nightly; alert on regression

**End-to-end tests** (Playwright driving Next.js):
- Happy path: tennis → Spain → full itinerary rendered
- Unknown sport (kabaddi) → LLM-assisted discovery fires
- Scraping failure mock → partial result, no crash

**Manual QA checklist**:
1. Tennis camp Spain August £2000 from London — full itinerary, budget met
2. Surf retreat Portugal £1500 beginner — accommodation_included detected, hotel skipped
3. Football tour Barcelona group 10 — group pricing handled
4. Niche sport (padel, kabaddi) — falls through to LLM-assisted discovery
5. Session continuity — preferences in turn 1 persist to turn 5
