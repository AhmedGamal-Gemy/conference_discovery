# Conference Discovery

Conference discovery agent that scrapes conference websites, extracts structured data via LLM prompts, enriches speaker data via Exa search, and validates conferences against configurable criteria (speaker count, travel time, dates). Built with Google ADK + Pydantic + LiteLLM.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Scrapling  │     │  LiteLLM     │     │  Mistral     │
│  MCP Server │────▶│  Proxy       │────▶│  API         │
│  :8017      │     │  :4000       │     │              │
└─────────────┘     └──────────────┘     └──────────────┘
       ▲                   ▲
       │  MCP SSE          │  OpenAI-compat
       │                   │
┌──────┴───────────────────┴──────────────────────────────────────┐
│                     ADK Workflow (9 steps)                       │
│                                                                  │
│  scrape → extract → discover → probe → merge → scrape_sub       │
│  → extract_sub → enrich_speakers → validate                     │
└──────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management
- Docker Desktop
- Node.js 20+ (for web frontend)
- Mistral API key (free tier works)

## Setup

### 1. Start Docker Infrastructure

```bash
# Start Scrapling MCP server
docker run -d -p 8017:8017 --name scrapling-mcp --restart unless-stopped \
  pyd4vinci/scrapling:latest mcp --http --port 8017

# Start LiteLLM proxy + database
docker compose up -d
```

Verify:

```bash
# Scrapling MCP
curl http://localhost:8017/mcp
# → {"jsonrpc":"2.0",...,"Not Acceptable: Client must accept text/event-stream"}

# LiteLLM proxy
curl http://localhost:4000/models \
  -H "Authorization: Bearer sk-GE_MBZsUSFrR3FQ86lZ8hg"
# → {"data":[{"id":"mistral-small",...}]}
```

### 2. Configure Environment

Create `conference_agent/.env`:

```env
MISTRAL_API_KEY=your-mistral-api-key-here
EXA_API_KEY=your-exa-api-key-here

LITELLM_PROXY_API_BASE=http://localhost:4000
LITELLM_PROXY_API_KEY=sk-GE_MBZsUSFrR3FQ86lZ8hg
PROXY_MASTER_KEY=sk-1234
```

### 3. Install Dependencies

```bash
uv pip install -e ".[extensions]"
```

## Running the Pipeline

### Full pipeline test

```bash
uv run python conference_agent/tests/test_orchestrator.py
```

Runs all 9 steps against a target URL:

```
scrape → extract → discover → probe → merge → scrape_sub
  → extract_sub → enrich_speakers → validate
```

### Individual step tests

```bash
uv run python conference_agent/tests/test_step1_scrape_homepage.py
uv run python conference_agent/tests/test_step2_extract_homepage.py
uv run python conference_agent/tools/scrapling_tool.py
```

## Running the Web UI

### Backend (FastAPI)

```bash
# Terminal 1
uv run uvicorn web.app:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend (Vite + React)

```bash
# Terminal 2
cd web/frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser. The frontend dev server proxies API calls to the backend on port 8001.

### Output

Pipeline outputs are saved to `output/intermediate/`:
- `orchestrator_HOMEPAGE_MARKDOWN.md` — raw scraped homepage
- `orchestrator_HOMEPAGE_DATA.json` — extracted conference data
- `orchestrator_DISCOVERED_LINKS.json` — all links found
- `orchestrator_PROBED_LINKS.md` — URL path probing results
- `orchestrator_SUB_PAGES_URLS.json` — merged sub-page URLs
- `orchestrator_SCRAPED_SUB_PAGES.md` — scraped sub-pages
- `orchestrator_SUB_PAGES_DATA.json` — extracted sub-page data
- `orchestrator_ENRICHMENT_STATUS.json` — speaker enrichment results
- `orchestrator_VALIDATION_DATA.json` — validation results

## Configuration

Edit `config/settings.yaml`:

| Key | Default | Description |
|-----|---------|-------------|
| `discovery.topic` | `"medical"` | Conference search topic |
| `validation.min_speakers` | `5` | Min speakers to pass validation |
| `validation.min_non_usa` | `2` | Min non-USA speakers required |
| `llm.extraction.model` | `mistral-large` | LLM for extraction steps |
| `llm.orchestrator.model` | `mistral-small` | LLM for orchestrator |
| `scrapling_mcp_url` | `http://localhost:8017/mcp` | Scrapling MCP endpoint |

## Troubleshooting

### LiteLLM proxy not responding
```bash
docker compose restart litellm-proxy
```

### Scrapling MCP server down
```bash
docker restart scrapling-mcp
```

### LLM calls fail with 429 (rate limited)
The LiteLLM proxy handles retries internally (up to 20 retries with exponential backoff). Configure in `proxy_config.yaml`.

## Project Structure

```
conference_discovery/
├── conference_agent/         # Core agent package
│   ├── steps/                # ADK step agents (9 pipeline steps)
│   │   ├── step1_scrape_homepage.py
│   │   ├── step2_extract_homepage.py
│   │   ├── step2_5_discover_links.py
│   │   ├── step2_6_probe_paths.py
│   │   ├── step3_merge_links.py
│   │   ├── step4_scrape_sub_pages.py
│   │   ├── step5_extract_sub_pages.py   # auto-chunks if >200K tokens
│   │   ├── step_enrich_speakers.py      # Exa-based speaker enrichment
│   │   ├── steps_enrich.py              # enrichment logic + lookups
│   │   ├── step6_validate.py            # 12 validation rules
│   │   ├── steps_validate.py            # validation logic
│   │   └── _callbacks.py               # shared LLM response callbacks
│   ├── tests/
│   │   ├── test_step1_scrape_homepage.py
│   │   ├── test_step2_extract_homepage.py
│   │   └── test_orchestrator.py
│   ├── agent.py              # Root LLM agent
│   ├── config.py             # SystemSettings (YAML + env)
│   ├── orchestrator.py       # ADK Workflow pipeline
│   ├── prompts/
│   │   └── extraction.py     # LLM extraction prompts (DRY resolver)
│   ├── schemas/              # Pydantic models
│   │   ├── conference.py
│   │   ├── homepage.py
│   │   ├── discovered_links.py
│   │   ├── speaker.py
│   │   ├── sub_pages_data.py
│   │   ├── venue.py
│   │   ├── registration.py
│   │   ├── validation.py
│   │   └── output_keys.py
│   └── tools/
│       ├── scrapling_tool.py # MCP client for stealthy_fetch
│       ├── path_probe.py     # URL path probing
│       ├── exa_tool.py       # Exa API wrapper
│       ├── discovery_tool.py
│       ├── date_extractor.py
│       ├── query_generator.py
│       ├── relevance_filter.py
│       └── intermediate_output.py
├── web/                      # Web UI (FastAPI + React)
│   ├── app.py                # FastAPI app factory
│   ├── main.py               # Entry point (uvicorn)
│   ├── api/                  # API routes (pipeline, discovery)
│   ├── services/             # Backend services
│   └── frontend/             # Vite + React + Tailwind
│       └── src/
│           ├── components/   # UI components
│           ├── pages/        # HomePage, SettingsPage
│           ├── hooks/        # usePipeline, useDiscovery
│           └── api/          # SSE + REST client
├── config/
│   └── settings.yaml         # All config (LLM, validation, etc.)
├── docker-compose.yml        # LiteLLM proxy + PostgreSQL
├── proxy_config.yaml         # LiteLLM proxy settings
├── output/
│   └── intermediate/         # Pipeline state snapshots
├── notes/                    # Research notes / schema viability
└── AGENTS.md                 # Project knowledge base for AI agents
```
```
