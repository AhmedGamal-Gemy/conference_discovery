# conference_agent/ KNOWLEDGE BASE

**Scope:** Core conference agent package — all components for the pipeline workflow.

## STRUCTURE

```text
conference_agent/
├── __init__.py
├── agent.py               # Root ADK LlmAgent (via LiteLlm proxy)
├── config.py              # SystemSettings + litellm proxy setup
├── orchestrator.py        # Workflow pipeline (9 steps)
├── prompts/
│   └── extraction.py      # LLM prompts ({markdown} placeholder)
├── schemas/               # Pydantic models (see schemas/AGENTS.md)
├── steps/                 # Workflow step agents
│   ├── step0_discover_conferences.py   # Exa search + LLM filter → DISCOVERY_RESULTS
│   ├── step1_scrape_homepage.py        # Fetch homepage via MCP
│   ├── step2_extract_homepage.py       # Extract HomepageData
│   ├── step2_5_discover_links.py       # Classify all homepage links
│   ├── step2_6_probe_paths.py          # Probe common URL paths
│   ├── step3_merge_links.py            # Merge → SubPages URLs
│   ├── step4_scrape_sub_pages.py       # Fetch sub-pages via bulk_stealthy_fetch
│   ├── step5_extract_sub_pages.py      # Extract speakers/venue/registration
│   └── step6_assemble_conference.py    # Assemble full Conference model
├── tests/                 # Pipeline tests
│   ├── test_step1_scrape_homepage.py
│   ├── test_step2_extract_homepage.py
│   └── test_orchestrator.py
└── tools/                 # MCP + utility tools
    ├── scrapling_tool.py     # MCP client for stealthy_fetch
    ├── path_probe.py         # URL path probing
    ├── discovery_tool.py     # Exa search + LLM relevance filter pipeline
    ├── exa_tool.py           # Exa API wrapper
    ├── query_generator.py    # Time-bounded search query generation
    ├── relevance_filter.py   # LLM relevance classifier (via LiteLLM proxy)
    └── intermediate_output.py # Session state → disk
```

## KEY COMPONENTS

### config.py
Central configuration. Loads settings from YAML + env via `SystemSettings`, then sets up LiteLLM proxy env vars (`LITELLM_PROXY_API_BASE`, `LITELLM_PROXY_API_KEY`). The `settings` singleton is safe to import from anywhere.

### orchestrator.py
`Workflow` (ADK 2.0 graph) with 9 sub-agents in sequence:
1. `discover_conferences` — Exa + LLM relevance filter → `DISCOVERY_RESULTS`
2. `scrape_homepage` → `HOMEPAGE_MARKDOWN`
3. `extract_homepage` → `HOMEPAGE_DATA`
4. `discover_links` → `DISCOVERED_LINKS`
5. `probe_paths` → `PROBED_LINKS`
6. `merge_links` → `SUB_PAGES_URLS`
7. `scrape_sub_pages` → `SCRAPED_SUB_PAGES`
8. `extract_sub_pages` → `SUB_PAGES_DATA`
9. `assemble_conference` → `CONFERENCE_DATA`

Each sub-agent `output_key` stores into the parent session state dict. All LLM calls go through the LiteLLM proxy, which handles rate limiting natively (max 20 retries, exponential backoff).

### tools/discovery_tool.py
Discovery pipeline used by Step 0. Chains: `generate_queries()` → Exa search per query → deduplicate by URL → concurrent LLM relevance filter → return `[{url, title}]`. Uses LiteLLM proxy (never calls Mistral directly).

### tools/scrapling_tool.py
Creates `McpToolset` using `StreamableHTTPConnectionParams` to connect to Scrapling MCP at `http://localhost:8017/mcp` (configured via `scrapling_mcp_url` in `config/settings.yaml`). Critical: includes `headers={"Accept": "application/json, text/event-stream"}` and `timeout=30.0` — without these, the MCP connection hangs or fails.

### tools/path_probe.py
Opens direct MCP sessions (not ADK tool routing) to probe common URL paths (`/speakers/`, `/venue/`, `/registration/`, etc.) on a conference website. Returns only paths with >100 chars content that don't match 404 patterns.

## STEP AGENTS

| Step | File | Agent Name | output_key | Notes |
|------|------|-----------|-----------|-------|
| 0 | `step0_discover_conferences.py` | `discover_conferences` | `DISCOVERY_RESULTS` | Exa search + LLM filter, tool-using LlmAgent |
| 1 | `step1_scrape_homepage.py` | `scrape_homepage_agent` | `HOMEPAGE_MARKDOWN` | Calls `stealthy_fetch`, 60s timeout, cloudflare bypass |
| 2 | `step2_extract_homepage.py` | `extract_homepage_agent` | `HOMEPAGE_DATA` | Extracts `HomepageData` via prompt |
| 2.5 | `step2_5_discover_links.py` | `discover_links_agent` | `DISCOVERED_LINKS` | Classifies all homepage links |
| 2.6 | `step2_6_probe_paths.py` | `probe_paths_agent` | `PROBED_LINKS` | Probes `/speakers/`, `/venue/`, etc. |
| 3 | `step3_merge_links.py` | `merge_links_agent` | `SUB_PAGES_URLS` | Merges discovered + probed links |
| 4 | `step4_scrape_sub_pages.py` | `scrape_sub_pages_agent` | `SCRAPED_SUB_PAGES` | Bulk fetch via `bulk_stealthy_fetch` |
| 5 | `step5_extract_sub_pages.py` | `extract_sub_pages_agent` | `SUB_PAGES_DATA` | Single LLM call, extracts all 3 sections |
| 6 | `step6_assemble_conference.py` | `assemble_conference_agent` | `CONFERENCE_DATA` | Composes full `Conference` model |

**Rate limiting**: LiteLLM proxy handles this natively (proxy_config.yaml: max retries 20, exponential backoff). No manual delay steps needed.

## SCHEMA CHANGES (P1 + P2 fixes)

### homepage.py — HomepageData
- Added `sector_tags: List[str] = []` — full topic list (replaces blunt `industry` single-label)
- `date_end` prompt now explicitly demands both range dates

### registration.py — RegistrationData
- Added `fee_range_usd: Optional[str]` — extracted fee range string
- Added `early_bird_deadline: Optional[str]` — early bird registration deadline

### conference.py — Conference
- Added `sector_tags: List[str]` (mirrors HomepageData)
- Added `fee_range_usd`, `early_bird_deadline` (mirrors RegistrationData)

### extraction.py — prompts
- `HOMEPAGE_EXTRACTION_PROMPT`: added `sector_tags` field + rule to prefer specific labels; end-date rule updated
- `REGISTRATION_EXTRACTION_PROMPT`: added `fee_range_usd` + `early_bird_deadline` extraction rules

## CONVENTIONS
- All LLM agents use `LiteLlm(model=settings.llm.extraction.model)` for proxy routing.
- `after_model_callback` strips markdown code blocks from LLM responses (in agents with `output_schema`).
- Agents with MCP tools do NOT use `output_schema` — ADK has a known conflict between tools + output_schema.
- Probed links step uses `FunctionTool(func=probe_common_paths)`, not MCP tools directly.
- Discovery tools (`relevance_filter.py`) route through LiteLLM proxy — never set `api_key` or `api_base` directly on litellm.
- All discovery tools rely on EXA_API_KEY being set in the environment before import (loaded by web/app.py or web/api/__init__.py).
