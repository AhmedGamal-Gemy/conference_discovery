# PROJECT KNOWLEDGE BASE

**Generated:** 2026-06-04
**Commit:** (current — post-LiteLLM proxy + pipeline fixes)
**Branch:** `feat/step1_scrape_homepage`

## OVERVIEW
Conference discovery agent that scrapes conference websites, extracts structured data via LLM prompts, and validates conferences against configurable criteria (speaker count, travel time, dates). Built with Google ADK + Pydantic + LiteLLM proxy.

## INFRASTRUCTURE
Three services must be running for the pipeline:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| Scrapling MCP | `pyd4vinci/scrapling:latest` | 8016 | Stealth web scraping (cloudflare bypass) |
| LiteLLM Proxy | `ghcr.io/berriai/litellm:main-latest` | 4000 | OpenAI-compatible proxy to Mistral |
| PostgreSQL | `postgres:16` | 5432 | LiteLLM usage/spend tracking |

## STRUCTURE
```
conference_discovery/
├── conference_agent/         # Core agent package
│   ├── steps/                # ADK step agents (orchestration pipeline)
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
│   ├── agent.py              # Root ADK LLM orchestrator (via proxy)
│   ├── config.py             # SystemSettings (YAML + env + LITELLM_PROXY config)
│   ├── orchestrator.py       # ADK SequentialAgent workflow (8 steps)
│   ├── prompts/
│   │   └── extraction.py     # LLM extraction prompts ({markdown} placeholder)
│   ├── schemas/              # Pydantic models
│   ├── tools/                # MCP toolsets + utility tools
├── config/
│   └── settings.yaml         # YAML settings (loaded by pydantic-settings)
├── docker-compose.yml        # LiteLLM proxy + PostgreSQL
├── proxy_config.yaml         # LiteLLM model + retry config
├── conference_agent/.env     # ALL secrets (API keys, proxy config)
├── output/
│   └── intermediate/         # Pipeline state snapshots
├── README.md
├── AGENTS.md
└── pyproject.toml             # Python 3.12+, google-adk, pydantic-settings
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add new conference data field | `conference_agent/schemas/*.py` | Pydantic models — add field, then update prompts |
| Change LLM model | `config/settings.yaml` → `llm.*.model` | Use bare names (`mistral-small`), no provider prefix |
| Add extraction prompt | `conference_agent/prompts/extraction.py` | Append new prompt template with `{markdown}` placeholder |
| Change validation thresholds | `config/settings.yaml` → `validation.*` | Loaded dynamically by `SystemSettings` in `config.py` |
| Add web scraping tool | `conference_agent/tools/` | Wrap as MCP toolset like `scrapling_tool.py` |
| Configure discovery sources | `config/settings.yaml` → `discovery.sources` | `exa`, `directories`, `org_websites` booleans |
| Debug scraping output | `output/intermediate/` | Pipeline state snapshots with `save_intermediate` |
| Research schema coverage | `notes/schema-viability.md` | Real-world test results against scraped conferences |
| Add sub-page discovery path | `conference_agent/tools/path_probe.py` | `paths` dict — key = path, value = category |
| Configure LiteLLM proxy | `proxy_config.yaml` | Model list, max retries, fallbacks |
| Set proxy env vars | `conference_agent/.env` | `LITELLM_PROXY_API_BASE`, `LITELLM_PROXY_API_KEY` |

## WORKFLOW (Orchestrator Pipeline)

The pipeline is a `SequentialAgent` running these 8 steps:

```
scrape_homepage  ──(output_key=URL, HOMEPAGE_MARKDOWN)──▶
       ↓
rate_limit_delay  ──(60s between LLM calls)──▶
       ↓
extract_homepage  ──(output_key=HOMEPAGE_DATA)──▶
       ↓
rate_limit_delay  ──(60s between LLM calls)──▶
       ↓
discover_links   ──(output_key=DISCOVERED_LINKS)──▶
       ↓
probe_paths      ──(output_key=PROBED_LINKS)──▶
       ↓
merge_links      ──(output_key=SUB_PAGES_URLS)──▶
       ↓
scrape_sub_pages ──(output_key=SCRAPED_SUB_PAGES)──▶
```

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `config.py` | module | `conference_agent/config.py` | Central config: SystemSettings + LITELLM_PROXY env setup |
| `orchestrator.py` | module | `conference_agent/orchestrator.py` | `SequentialAgent` chaining all 8 pipeline steps |
| `root_agent` | LlmAgent | `conference_agent/agent.py` | Root LLM agent (reserved for future orchestration dispatch) |
| `settings` | SystemSettings | `conference_agent/config.py` | Singleton — import everywhere (not just `conference_agent` module) |
| `Conference` | model | `conference_agent/schemas/conference.py` | Top-level composed model |
| `HomepageData` | model | `conference_agent/schemas/homepage.py` | Homepage extraction target |
| `DiscoveredLinksData` | model | `conference_agent/schemas/discovered_links.py` | Link classification output |
| `SubPages` | model | `conference_agent/schemas/homepage.py` | URLs for speakers, venue, registration |
| `output_keys` | StrEnum | `conference_agent/schemas/output_keys.py` | Session state keys (explicit uppercase values) |
| `scrapling_toolset` | McpToolset | `conference_agent/tools/scrapling_tool.py` | MCP client with headers + timeout fix |
| `scrape_homepage_agent` | LlmAgent | `conference_agent/steps/step1_scrape_homepage.py` | Step 1: fetch via MCP |
| `extract_homepage_agent` | LlmAgent | `conference_agent/steps/step2_extract_homepage.py` | Step 2: extract HomepageData |
| `discover_links_agent` | LlmAgent | `conference_agent/steps/step2_5_discover_links.py` | Step 2.5: classify links from homepage |
| `probe_paths_agent` | LlmAgent | `conference_agent/steps/step2_6_probe_paths.py` | Step 2.6: probe common URL paths |
| `merge_links_agent` | LlmAgent | `conference_agent/steps/step3_merge_links.py` | Step 3: merge → SubPages URLs |
| `scrape_sub_pages_agent` | LlmAgent | `conference_agent/steps/step4_scrape_sub_pages.py` | Step 4: fetch sub-pages via MCP |
| `rate_limit_delay_agent` | BaseAgent | `conference_agent/steps/step_rate_limit_delay.py` | Exponential backoff between LLM calls |

## CONVENTIONS
- **Settings hierarchy**: `init_settings > env_settings > YAML > dotenv` (explicit in `SystemSettings.settings_customise_sources`). LiteLLM proxy config lives in `config.py` after settings init.
- **LLM routing**: All LLM calls go through LiteLLM proxy at `localhost:4000`. Proxy handles retries (up to 20), fallbacks, and rate limiting.
- **Model names**: Bare names in settings (`mistral-small`), NOT `mistral/mistral-small-latest`. The proxy resolves provider prefixes.
- **Output keys**: `StrEnum` auto() produces lowercase strings that don't match prompt `{state.URL}` placeholders. Use explicit string values.
- **Prompt placeholders**: All extraction prompts use `{markdown}` as the single template variable.
- **Rate limiting**: Exponential backoff with `delay = min(30 × attempt^1.5, 300)` between LLM calls. Attempt counter stored in session state.
- **MCP headers**: Scrapling MCP requires `Accept: application/json, text/event-stream` in HTTP connection params.
- **Pydantic models for everything**: Inputs, outputs, and config are all strictly typed Pydantic models.

## ANTI-PATTERNS (THIS PROJECT)
- **DO NOT hardcode config values** — always use `settings` singleton from `config.py`.
- **DO NOT set `litellm.api_base`/`litellm.api_key` directly** — use `use_litellm_proxy = True` with `LITELLM_PROXY_API_BASE`/`LITELLM_PROXY_API_KEY` env vars.
- **DO NOT skip `speakers_confirmed` check** — an empty speaker list is different from unconfirmed speakers.
- **DO NOT geocode before confirming speakers exist** — `travel_hours`, `is_local`, `is_usa` are blocked until geocoding step.
- **NEVER return markdown backticks in LLM prompts** — extraction prompts explicitly demand raw JSON only.
- **NEVER store secrets in settings.yaml** — use `conference_agent/.env`.
- **DO NOT put 2+ LLM-heavy agents back-to-back** — always insert `rate_limit_delay_agent` between them.

## UNIQUE STYLES
- **MCP-first tooling**: Web scraping is an external MCP server (`scrapling_mcp_url`), not a local dependency. Agent uses `McpToolset` + `StreamableHTTPConnectionParams` with explicit Accept header.
- **Prompt-driven extraction**: No HTML parsers — all structured data extraction is LLM-prompt-based with strict JSON schemas.
- **Workflow pipeline**: Uses ADK's `SequentialAgent` (not `PipelineStep`) to chain agents by `output_key`.
- **Direct MCP for path probing**: `path_probe.py` opens raw MCP sessions (not ADK tool routing) for sub-page probing with per-request timeouts.

## COMMANDS
```bash
# Start Docker infrastructure
docker run -d -p 8016:8016 --name scrapling-mcp --restart unless-stopped \
  pyd4vinci/scrapling:latest mcp --http --port 8016
docker compose up -d

# Run agent entry point
python -m conference_agent

# Test standalone scrapling
python conference_agent/tools/scrapling_tool.py

# Test individual steps
uv run python conference_agent/tests/test_step1_scrape_homepage.py
uv run python conference_agent/tests/test_step2_extract_homepage.py

# Test full pipeline
uv run python conference_agent/tests/test_orchestrator.py

# Install with dev dependencies
uv pip install -e ".[extensions]"
```

## NOTES
- `main.py` is currently a stub (`print("Hello from conference-discovery!")`). Real entry point is `conference_agent/` package.
- Scrapling MCP server must be running locally at `http://localhost:8016/mcp`. Use `--http --port 8016` flags; default `stdio` transport won't work with ADK.
- `conference_agent/.env` contains ALL secrets. Do NOT commit to git (already in `.gitignore`).
- `output/intermediate/` saves pipeline state snapshots via `save_intermediate` tool.
- Tests live in `conference_agent/tests/` (root `tests/` removed).
- `database/` is reserved for future persistence layer.
- **output_key behavior**: On sub-agents within a `SequentialAgent`, `output_key` stores in parent session state (as dict, not Pydantic model). Validate with `Model.model_validate(state[key])` when reading back.
- **Rate limiting**: Mistral free tier is strict. Pipeline includes exponential-backoff delay steps between LLM-heavy agents.
- **Zombie Docker containers**: `docker stop`/`docker rm -f` may hang if container process is zombie. Use `wsl --shutdown` as last resort.
