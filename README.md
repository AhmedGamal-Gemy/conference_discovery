# Conference Discovery

Conference discovery agent that scrapes conference websites, extracts structured data via LLM prompts, and validates conferences against configurable criteria (speaker count, travel time, dates).

Built with **Google ADK** + **Pydantic** + **LiteLLM proxy** + **Scrapling MCP**.

## Architecture

```
┌──────────────┐         ┌──────────────┐         ┌───────────┐
│  Scrapling   │───MCP──▶│  LiteLLM     │──OpenAI─▶│  Mistral  │
│  MCP Server  │  SSE    │  Proxy       │ compat   │  API      │
│  :8017       │         │  :4000       │          │           │
└──────────────┘         └──────────────┘         └───────────┘
                                                        ▲
                                                         │  LLM calls
                          ┌──────────────────────────────┘
                          │
                    ┌─────┴──────────────────────────────────┐
                    │  ADK Workflow Pipeline (8 steps)        │
                    │                                        │
                    │  1. scrape_homepage                     │
                    │  2. extract_homepage                    │
                    │  3. discover_links                      │
                    │  4. probe_paths                         │
                    │  5. merge_links                         │
                    │  6. scrape_sub_pages                    │
                    │  7. extract_sub_pages                   │
                    │  8. assemble_conference                 │
                    └────────────────────────────────────────┘
```

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Runtime |
| [uv](https://docs.astral.sh/uv/) | latest | Dependency management |
| Docker Desktop | — | LiteLLM proxy + PostgreSQL + Scrapling MCP |
| Mistral API key | — | LLM provider (free tier works) |

---

## Quick Start

```bash
# 1. Clone + install
git clone <repo-url> && cd conference_discovery
cp conference_agent/.env.example conference_agent/.env   # then fill in your keys
uv pip install -e ".[extensions]"

# 2. Start Docker infrastructure
docker compose up -d

# 3. Run the full pipeline against any conference URL
uv run python run_pipeline.py https://2026.emnlp.org/
```

That's it. The pipeline scrapes, extracts, discovers links, probes sub-pages, and assembles a structured `Conference` object.

---

## Setup (detailed)

### 1. Environment variables

Copy the example file and fill in real values:

```bash
cp conference_agent/.env.example conference_agent/.env
```

| Variable | Required | Description |
|----------|----------|-------------|
| `MISTRAL_API_KEY` | ✅ | Your Mistral API key (get one at [console.mistral.ai](https://console.mistral.ai)) |
| `EXA_API_KEY` | ✅ (for discovery) | Exa search API key (get one at [exa.ai](https://exa.ai)) |
| `LITELLM_PROXY_API_KEY` | ✅ | Must match `master_key` in `proxy_config.yaml` |
| `LITELLM_PROXY_API_BASE` | optional | Defaults to `http://localhost:4000` |

### 2. Start services

```bash
docker compose up -d
```

Three services start automatically:

| Service | Port | Purpose |
|---------|------|---------|
| `scrapling-mcp` | 8017 | Stealth web scraping (Cloudflare bypass) |
| `litellm-proxy` | 4000 | OpenAI-compatible proxy to Mistral |
| `db` (PostgreSQL 16) | 5432 | LiteLLM usage/spend tracking |

Verify they're running:

```bash
# Scrapling MCP — returns "Not Acceptable: Client must accept text/event-stream" on plain HTTP (expected)
curl -H "Accept: text/event-stream" http://localhost:8017/mcp

# LiteLLM proxy
curl http://localhost:4000/models
```

### 3. Install dependencies

```bash
uv pip install -e ".[extensions]"
```

---

## Running the Pipeline

### Full pipeline CLI (recommended)

```bash
uv run python run_pipeline.py <URL>
```

Runs all 8 steps end-to-end and prints a summary of the assembled `Conference` object. Output saved to `output/intermediate/`.

Default URL if none provided: `https://2026.emnlp.org/`

### Individual step tests

```bash
# Step 1: scrape homepage
uv run python conference_agent/tests/test_step1_scrape_homepage.py

# Step 2: extract structured data from markdown
uv run python conference_agent/tests/test_step2_extract_homepage.py

# Full pipeline (pytest style, no CLI args)
uv run python conference_agent/tests/test_orchestrator.py
```

### Web API

```bash
# Start the FastAPI web server (port 8001)
uv run python web/main.py
```

---

## Configuration

All tuning lives in `config/settings.yaml`. Key knobs:

| Key | Default | Description |
|-----|---------|-------------|
| `discovery.topic` | `"medical"` | Search topic for conference discovery |
| `discovery.months_ahead` | `3` | How many months ahead to look |
| `validation.min_speakers` | `5` | Min confirmed speakers to pass |
| `validation.min_non_local` | `5` | Min non-local speakers for US/local classification |
| `validation.min_travel_hours` | `4` | Min travel hours to be considered "non-local" |
| `llm.orchestrator.model` | `"mistral-small"` | Model for orchestration steps |
| `llm.extraction.temperature` | `0.1` | Temperature for extraction (lower = more deterministic) |

LLM retry behavior: configured in `proxy_config.yaml` (`num_retries: 20`, exponential backoff). The proxy handles rate limiting — no client-side delays needed.

---

## Project Structure

```
conference_discovery/
├── conference_agent/            # Core agent package
│   ├── steps/                   # ADK step agents (8-step pipeline)
│   │   ├── step1_scrape_homepage.py
│   │   ├── step2_extract_homepage.py
│   │   ├── step2_5_discover_links.py
│   │   ├── step2_6_probe_paths.py
│   │   ├── step3_merge_links.py
│   │   ├── step4_scrape_sub_pages.py
│   │   ├── step5_extract_sub_pages.py
│   │   └── step6_assemble_conference.py
│   ├── tests/                   # Test suite
│   │   ├── test_step1_scrape_homepage.py
│   │   ├── test_step2_extract_homepage.py
│   │   └── test_orchestrator.py
│   ├── agent.py                 # Root ADK LlmAgent
│   ├── config.py                # SystemSettings + LiteLLM proxy setup
│   ├── orchestrator.py          # Workflow pipeline (8 steps)
│   ├── prompts/                 # LLM extraction prompt templates
│   ├── schemas/                 # Pydantic models (Conference, HomepageData, …)
│   └── tools/                   # MCP + utility tools
│       ├── scrapling_tool.py    # MCP client for stealthy_fetch
│       ├── path_probe.py        # URL path probing
│       ├── discovery_tool.py    # Exa search
│       ├── exa_tool.py          # Exa API wrapper
│       ├── query_generator.py   # Search query generation
│       ├── relevance_filter.py  # Relevance scoring
│       └── intermediate_output.py # Session state → disk
├── web/                         # FastAPI web app (port 8001)
│   ├── main.py                  # App entry point
│   ├── app.py                   # FastAPI app factory
│   ├── api/                     # Route handlers
│   ├── schemas.py               # API schemas
│   ├── services/                # Business logic
│   └── frontend/                # Frontend assets
├── config/
│   └── settings.yaml            # YAML settings (LLM, validation, discovery)
├── output/
│   └── intermediate/            # Pipeline state snapshots (gitignored)
├── docker-compose.yml           # All infra (Scrapling, LiteLLM, PostgreSQL)
├── proxy_config.yaml            # LiteLLM model list + retry config
├── run_pipeline.py              # CLI entry point for the full pipeline
├── main.py                      # Project entry point
└── pyproject.toml               # Package metadata + dependencies
```

---

## Troubleshooting

### LiteLLM proxy not responding
```bash
docker compose restart litellm-proxy
docker compose logs litellm-proxy   # inspect logs
```

### Scrapling MCP server down
```bash
docker restart scrapling-mcp
docker logs scrapling-mcp
```

### LLM calls fail with 429 (rate limited)
The LiteLLM proxy handles retries internally (up to 20 per `proxy_config.yaml`). If you're hitting limits, consider reducing `rpm` or increasing `num_retries`.

### Zombie Docker containers won't stop
```bash
wsl --shutdown   # Windows only — last resort for hung containers
```

---

## Key Conventions

- **Settings hierarchy**: `init > env > YAML > dotenv` (explicit in `SystemSettings.settings_customise_sources`)
- **All LLM calls route through LiteLLM proxy** at `localhost:4000` — never set `litellm.api_base` directly
- **Model names are bare**: use `"mistral-small"` in config, the proxy resolves the provider prefix
- **MCP headers**: Scrapling requires `Accept: application/json, text/event-stream` in connection params
- **Never store secrets in `settings.yaml`** — use `conference_agent/.env` (already in `.gitignore`)
