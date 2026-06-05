# Heill

AI-powered sports travel agent. Plan complete sports holidays — flights, accommodation, and the sporting activity itself — through a natural-language chat interface.

Activities are sourced from a curated catalogue (`heill/data/sportscations.yaml`) that you control. Add your available packages to the file and the agent will match and recommend them to users.

![Chat UI](https://placehold.co/800x400?text=Heill+Chat+UI)

---

## Features

- **Curated sportscation catalogue** — define available packages in `heill/data/sportscations.yaml`; no web scraping
- **Natural language responses** — the agent replies conversationally, not with raw JSON
- **Flights & accommodation** — scrapes Google Flights and Booking.com
- **Exchange rates** — live currency conversion
- **Streaming chat** — tokens stream to the UI as they're generated
- **Tool status banners** — shows "Searching sport activities…" in real time
- **Session persistence** — conversation context stored in Supabase across turns

---

## Tech Stack

| Layer | Choice |
|---|---|
| LLM | [Ollama](https://ollama.com) (`llama3.1:8b`, local, free) |
| Backend | FastAPI (Python 3.12), streaming SSE |
| Agent loop | Custom `heill/agent.py` — OpenAI-compatible tool use |
| Session store | Supabase (PostgreSQL, JSONB) |
| Activity catalogue | `heill/data/sportscations.yaml` — YAML file you populate |
| Scraping | httpx + BeautifulSoup (flights/accommodation), Playwright (fallback) |
| Frontend | Next.js 14 + Tailwind CSS |

---

## Prerequisites

- Python 3.12+ (on macOS: `brew install python@3.12`)
- Node.js 18+
- [Ollama](https://ollama.com/download) — download the official installer, **not** `brew install ollama` (the Homebrew package is missing required binaries)
- A [Supabase](https://supabase.com) project

---

## Setup

### 1. Clone

```bash
git clone https://github.com/Mapleying/heill.git
cd heill
```

### 2. Environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your Supabase credentials (get them from **Project Settings → API** in the Supabase dashboard):

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1:8b
```

### 3. Supabase — create the sessions table

Run the migration in the Supabase SQL editor:

```bash
# via Supabase CLI
supabase link --project-ref your-project-ref
supabase db push
```

Or paste the contents of `supabase/migrations/001_sessions.sql` directly into the **SQL Editor** in the Supabase dashboard.

### 4. Pull the LLM model

```bash
ollama pull llama3.1:8b
```

> On 8 GB RAM, `llama3.2:3b` is faster but less accurate at following natural language output instructions.

### 5. Python backend

```bash
# Use the Homebrew Python 3.12 explicitly (macOS ships with 3.9)
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 6. Frontend

```bash
cd frontend
npm install
```

> **Note:** The frontend uses a Next.js Route Handler (`app/api/chat/route.ts`) to proxy SSE from the FastAPI backend. Do not replace this with a `next.config.js` rewrite — rewrites buffer response bodies and will break streaming.

---

## Running

Open three terminals:

```bash
# Terminal 1 — Ollama
ollama serve

# Terminal 2 — API (from project root)
source .venv/bin/activate
set -a && source .env && set +a
uvicorn heill.main:app --reload --port 8000

# Terminal 3 — Frontend
cd frontend
npm run dev
```

Open **http://localhost:3000** (or `:3001` if 3000 is already in use — Next.js will print the actual URL in the terminal) and start planning.

---

## Adding sportscation packages

Edit `heill/data/sportscations.yaml` to add the packages you want to offer. Each entry looks like:

```yaml
- id: tennis-mallorca-001
  sport: tennis
  provider_name: "Mallorca Tennis Academy"
  title: "Intensive Tennis Camp – Mallorca"
  location: "Mallorca, Spain"
  country: Spain
  region: Balearic Islands
  activity_type: camp          # camp | clinic | retreat | tour | course
  skill_levels: [intermediate, advanced]
  duration_days: 7
  price_per_person: 1200
  currency: EUR
  includes_accommodation: false
  dates:
    - "2025-08-01 to 2025-08-07"
  url: "https://yourwebsite.com/tennis-mallorca"
  description: "7-day intensive tennis program on outdoor clay courts."
  tags: [mallorca, spain, mediterranean]
```

The `tags` field helps with location matching — add nearby places or alternate spellings.

---

## Example queries

- *Tennis camp in Shanghai, June 2026*
- *Surf retreat in Portugal, beginner, 1 week in September*
- *Golf break in Scotland, 4 nights, flying from Manchester*
- *Ski holiday in the Alps, family of 3, February*

---

## Project Structure

```
heill/
├── heill/
│   ├── agent.py              # Streaming agentic loop (tool use)
│   ├── main.py               # FastAPI — /chat SSE, /sessions CRUD
│   ├── session.py            # Supabase session CRUD
│   ├── prompts.py            # System prompt
│   ├── data/
│   │   └── sportscations.yaml    # Curated activity catalogue — edit this to add packages
│   ├── tools/
│   │   ├── registry.py       # Tool dispatch + OpenAI function schemas
│   │   ├── sport_activities.py  # Primary tool — looks up sportscations.yaml
│   │   ├── web_search.py     # DuckDuckGo / SerpAPI
│   │   ├── browse_page.py    # httpx + BS4 → Playwright fallback
│   │   ├── flights.py        # Google Flights scraper
│   │   ├── accommodation.py  # Booking.com scraper
│   │   └── exchange_rate.py  # exchangerate-api.com
│   └── scrapers/
│       └── browser_pool.py        # Playwright async pool
├── frontend/
│   ├── app/chat/             # Chat page + components
│   └── hooks/useHeillChat.ts # Custom SSE hook
└── supabase/
    └── migrations/001_sessions.sql
```

---

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat` | Send a message; returns SSE stream |
| `GET` | `/sessions/{id}` | Retrieve a session |
| `DELETE` | `/sessions/{id}` | Delete a session |
| `GET` | `/health` | Health check |

**POST /chat request body:**
```json
{ "session_id": "optional-uuid", "message": "Tennis camp in Spain..." }
```

**SSE event types:**
```
{"type": "session_id", "session_id": "..."}
{"type": "text", "content": "..."}
{"type": "tool_start", "tool": "find_sport_activities", "tool_id": "..."}
{"type": "tool_end", "tool": "find_sport_activities", "tool_id": "..."}
{"type": "done"}
```

---

## Using a different LLM

Any OpenAI-compatible endpoint works. Update `.env`:

```env
# OpenAI
OLLAMA_BASE_URL=https://api.openai.com/v1
OLLAMA_MODEL=gpt-4o
# set OPENAI_API_KEY in your environment

# Anthropic (via proxy)
# or swap agent.py back to the Anthropic SDK
```

---

## Licence

MIT
