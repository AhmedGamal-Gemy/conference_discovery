# conference_agent/ KNOWLEDGE BASE

**Scope:** Core conference agent package — all components for the pipeline workflow.

## STRUCTURE

```
conference_agent/
├── __init__.py
├── agent.py                 # Root ADK LlmAgent (via LiteLlm proxy)
├── config.py                # SystemSettings + litellm proxy setup
├── orchestrator.py          # SequentialAgent pipeline (8 steps)
├── prompts/
│   └── extraction.py        # LLM prompts ({markdown} placeholder)
├── schemas/                 # Pydantic models (see schemas/AGENTS.md)
├── steps/                   # Workflow step agents
│   ├── step1_scrape_homepage.py
│   ├── step2_extract_homepage.py
│   ├── step2_5_discover_links.py
│   ├── step2_6_probe_paths.py
│   ├── step3_merge_links.py
│   ├── step4_scrape_sub_pages.py
│   └── step_rate_limit_delay.py
├── tests/                   # Pipeline tests
│   ├── test_step1_scrape_homepage.py
│   ├── test_step2_extract_homepage.py
│   └── test_orchestrator.py
└── tools/                   # MCP + utility tools
    ├── scrapling_tool.py
    ├── path_probe.py
    ├── discovery_tool.py
    ├── exa_tool.py
    ├── query_generator.py
    ├── relevance_filter.py
    └── intermediate_output.py
```

## KEY COMPONENTS

### config.py
Central configuration. Loads settings from YAML + env via `SystemSettings`, then sets up LiteLLM proxy env vars (`LITELLM_PROXY_API_BASE`, `LITELLM_PROXY_API_KEY`). The `settings` singleton is safe to import from anywhere.

### orchestrator.py
`SequentialAgent` with 8 sub-agents in sequence. Each sub-agent `output_key` stores into the parent session state dict. The two `rate_limit_delay_agent` instances are separate `BaseAgent` objects with independent attempt counters (each starts at attempt=1).

### steps/step_rate_limit_delay.py
Exponential backoff: `delay = min(30 × attempt^1.5, 300)`. Reads/writes `rate_limit_attempts` counter from session state. Each instance tracks its own counter.

### tools/scrapling_tool.py
Creates `McpToolset` using `StreamableHTTPConnectionParams` to connect to Scrapling MCP at `http://localhost:8016/mcp`. Critical: includes `headers={"Accept": "application/json, text/event-stream"}` and `timeout=30.0` — without these, the MCP connection hangs or fails.

### tools/path_probe.py
Opens direct MCP sessions (not ADK tool routing) to probe common URL paths (`/speakers/`, `/venue/`, `/registration/`, etc.) on a conference website. Returns only paths with >100 chars content that don't match 404 patterns.

## STEP AGENTS

| Step | File | Agent Name | Type | output_key | Notes |
|------|------|-----------|------|-----------|-------|
| 1 | `step1_scrape_homepage.py` | `scrape_homepage_agent` | LlmAgent | URL, HOMEPAGE_MARKDOWN | Calls `stealthy_fetch` with 60s timeout, cloudflare bypass |
| Delay | `step_rate_limit_delay.py` | `rate_limit_delay_agent` | BaseAgent | (none) | Exponential backoff (30s base, 1.5x exp, max 300s) |
| 2 | `step2_extract_homepage.py` | `extract_homepage_agent` | LlmAgent | HOMEPAGE_DATA | Extracts `HomepageData` via prompt |
| Delay | `step_rate_limit_delay.py` | `rate_limit_delay_agent2` | BaseAgent | (none) | Separate attempt counter from first delay |
| 2.5 | `step2_5_discover_links.py` | `discover_links_agent` | LlmAgent | DISCOVERED_LINKS | Classifies all homepage links |
| 2.6 | `step2_6_probe_paths.py` | `probe_paths_agent` | LlmAgent | PROBED_LINKS | Probes `/speakers/`, `/venue/`, etc. via path_probe tool |
| 3 | `step3_merge_links.py` | `merge_links_agent` | LlmAgent | SUB_PAGES_URLS | Merges discovered+probed links into SubPages |
| 4 | `step4_scrape_sub_pages.py` | `scrape_sub_pages_agent` | LlmAgent | SCRAPED_SUB_PAGES | Fetches speakers/venue/registration URLs |

## CONVENTIONS
- All LLM agents use `LiteLlm(model=settings.llm.extraction.model)` for proxy routing.
- `after_model_callback` strips markdown code blocks from LLM responses (in agents with `output_schema`).
- Agents with MCP tools do NOT use `output_schema` — ADK has a known conflict between tools + output_schema.
- Probed links step uses `FunctionTool(func=probe_common_paths)`, not MCP tools directly.
