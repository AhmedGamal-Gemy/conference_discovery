# Conference Discovery

Conference discovery agent that scrapes conference websites, extracts structured data via LLM prompts, and validates conferences against configurable criteria (speaker count, travel time, dates). Built with Google ADK + Pydantic + LiteLLM.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Scrapling  │     │  LiteLLM     │     │  Mistral     │
│  MCP Server │────▶│  Proxy       │────▶│  API         │
│  :8016      │     │  :4000       │     │              │
└─────────────┘     └──────────────┘     └──────────────┘
       ▲                   ▲
       │  MCP SSE          │  OpenAI-compat
       │                   │
┌──────┴───────────────────┴──────────────────────────┐
│                 ADK Workflow                        │
│                                                      │
│  scrape → delay → extract → delay → discover       │
│  → probe → merge → scrape_sub_pages                 │
└──────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management
- Docker Desktop
- Mistral API key (free tier works)

## Setup

### 1. Start Docker Infrastructure

Start all services (Scrapling MCP, LiteLLM proxy, PostgreSQL):

```bash
# Start Scrapling MCP server
docker run -d -p 8016:8016 --name scrapling-mcp --restart unless-stopped \
  pyd4vinci/scrapling:latest mcp --http --port 8016

# Start LiteLLM proxy + database
docker compose up -d
```

Verify both are running:

```bash
# Scrapling MCP (expects SSE — returns expected error on plain HTTP)
curl http://localhost:8016/mcp
# → {"jsonrpc":"2.0",...,"Not Acceptable: Client must accept text/event-stream"}

# LiteLLM proxy
curl http://localhost:4000/models \
  -H "Authorization: Bearer sk-GE_MBZsUSFrR3FQ86lZ8hg"
# → {"data":[{"id":"mistral-small",...}]}
```

### 2. Configure Environment

Create `conference_agent/.env` (already exists if cloned with secrets):

```env
MISTRAL_API_KEY=your-mistral-api-key-here
EXA_API_KEY=your-exa-api-key-here

# LiteLLM Proxy Configuration
LITELLM_PROXY_API_BASE=http://localhost:4000
LITELLM_PROXY_API_KEY=sk-GE_MBZsUSFrR3FQ86lZ8hg
PROXY_MASTER_KEY=sk-1234
```

### 3. Install Dependencies

```bash
uv pip install -e ".[extensions]"
```

## Running the Pipeline

### Full pipeline test (recommended)

```bash
uv run python conference_agent/tests/test_orchestrator.py
```

This runs all 8 workflow steps against a target URL and validates output:

```
scrape → [30s delay] → extract → [30s delay] → discover → probe → merge → scrape_sub_pages
```

### Individual step tests

```bash
# Step 1: scrape homepage via Scrapling MCP
uv run python conference_agent/tests/test_step1_scrape_homepage.py

# Step 2: extract structured data from markdown
uv run python conference_agent/tests/test_step2_extract_homepage.py

# Test scrapling tool directly
uv run python conference_agent/tools/scrapling_tool.py
```

### Output

Pipeline outputs are saved to `output/intermediate/`:
- `orchestrator_HOMEPAGE_MARKDOWN.md` — raw scraped homepage
- `orchestrator_HOMEPAGE_DATA.json` — extracted conference data
- `orchestrator_DISCOVERED_LINKS.json` — all links found
- `orchestrator_PROBED_LINKS.md` — URL path probing results
- `orchestrator_SUB_PAGES_URLS.json` — merged sub-page URLs
- `orchestrator_SCRAPED_SUB_PAGES.md` — scraped speakers/venue/registration

## Configuration

Edit `config/settings.yaml`:

| Key | Default | Description |
|-----|---------|-------------|
| `discovery.topic` | `"medical"` | Conference search topic |
| `validation.min_speakers` | `5` | Min speakers to pass validation |
| `validation.min_travel_hours` | `4` | Min travel hours from local |
| `llm.orchestrator.model` | `mistral-small` | LLM model (via proxy) |
| `llm.extraction.temperature` | `0.1` | Extraction LLM temperature |

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
The exponential backoff delay (30s base, 1.5x exponent, max 300s) handles this automatically. The LiteLLM proxy also retries internally (up to 20 retries with backoff).

## Project Structure

```
conference_discovery/
├── conference_agent/         # Core agent package
│   ├── steps/                # ADK step agents
│   │   ├── step1_scrape_homepage.py
│   │   ├── step2_extract_homepage.py
│   │   ├── step2_5_discover_links.py
│   │   ├── step2_6_probe_paths.py
│   │   ├── step3_merge_links.py
│   │   ├── step4_scrape_sub_pages.py
│   │   └── step_rate_limit_delay.py
│   ├── tests/
│   │   ├── test_step1_scrape_homepage.py
│   │   ├── test_step2_extract_homepage.py
│   │   └── test_orchestrator.py
│   ├── agent.py              # Root LLM agent
│   ├── config.py             # SystemSettings (YAML + env)
│   ├── orchestrator.py       # Workflow pipeline
│   ├── prompts/
│   │   └── extraction.py     # LLM extraction prompts
│   ├── schemas/              # Pydantic models
│   │   ├── conference.py
│   │   ├── homepage.py
│   │   ├── discovered_links.py
│   │   ├── speaker.py
│   │   ├── venue.py
│   │   ├── registration.py
│   │   ├── validation.py
│   │   └── output_keys.py
│   └── tools/
│       ├── scrapling_tool.py # MCP client for stealthy_fetch
│       ├── path_probe.py     # URL path probing
│       ├── discovery_tool.py # Exa search
│       ├── exa_tool.py       # Exa API wrapper
│       ├── query_generator.py
│       ├── relevance_filter.py
│       └── intermediate_output.py
├── config/
│   └── settings.yaml         # All config (LLM, validation, etc.)
├── docker-compose.yml        # LiteLLM proxy + PostgreSQL
├── proxy_config.yaml         # LiteLLM proxy settings
├── output/
│   └── intermediate/         # Pipeline state snapshots
└── main.py                   # Entry point (stub)
```
