# PROJECT KNOWLEDGE BASE

**Generated:** 2026-05-24
**Commit:** a59ac26
**Branch:** feature/test

## OVERVIEW
Conference discovery agent that scrapes conference websites, extracts structured data via LLM prompts, and validates conferences against configurable criteria (speaker count, travel time, dates). Built with Google ADK + Pydantic.

## STRUCTURE
```
conference_discovery/
├── conference_agent/    # Core agent package
│   ├── steps/           # ADK step agents (orchestration pipeline)
│   ├── tests/           # Test suite
│   ├── agent.py         # Root ADK orchestrator
│   ├── config.py        # SystemSettings (YAML + env + init priority)
│   ├── prompts/         # LLM extraction prompts
│   ├── schemas/         # Pydantic data models
│   └── tools/           # MCP toolsets
├── config/              # YAML settings (settings.yaml loaded by pydantic-settings)
├── database/            # (empty — TBD persistence layer)
├── notes/               # Research notes (schema-viability.md)
├── output/              # Scraping results + generated reports
├── main.py              # Entry point (currently stub)
├── pyproject.toml       # Python 3.12+, google-adk, pydantic-settings
└── requirements.txt     # (empty — deps in pyproject.toml)
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add new conference data field | `conference_agent/schemas/*.py` | Pydantic models — add field, then update prompts |
| Change LLM model | `config/settings.yaml` → `llm.*.model` | Also check `conference_agent/agent.py` root_agent model |
| Add extraction prompt | `conference_agent/prompts/extraction.py` | Append new prompt template with `{markdown}` placeholder |
| Change validation thresholds | `config/settings.yaml` → `validation.*` | Loaded dynamically by `SystemSettings` in `config.py` |
| Add web scraping tool | `conference_agent/tools/` | Wrap as MCP toolset like `scrapling_tool.py` |
| Configure discovery sources | `config/settings.yaml` → `discovery.sources` | `exa`, `directories`, `org_websites` booleans |
| Debug scraping output | `output/scrapling_*.md` | Raw markdown from `stealthy_fetch` |
| Research schema coverage | `notes/schema-viability.md` | Real-world test results against scraped conferences |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `root_agent` | Agent | `conference_agent/agent.py:4` | Google ADK LLM orchestrator (Mistral) |
| `SystemSettings` | class | `conference_agent/config.py:62` | Pydantic-settings with YAML + env + init priority |
| `settings` | instance | `conference_agent/config.py:95` | Singleton config — import everywhere |
| `Conference` | model | `conference_agent/schemas/conference.py:10` | Top-level composed model |
| `HomepageData` | model | `conference_agent/schemas/homepage.py:12` | Conference homepage extraction target |
| `SpeakersData` | model | `conference_agent/schemas/speaker.py:21` | Speakers page extraction target |
| `VenueData` | model | `conference_agent/schemas/venue.py:5` | Venue page extraction target |
| `RegistrationData` | model | `conference_agent/schemas/registration.py:4` | Registration page extraction target |
| `ValidationResult` | model | `conference_agent/schemas/validation.py:5` | Pass/fail with rejection reason |
| `scrapling_toolset` | McpToolset | `conference_agent/tools/scrapling_tool.py:7` | MCP client for `stealthy_fetch` |
| `scrape_homepage_agent` | LlmAgent | `conference_agent/steps/step1_scrape_homepage.py:11` | Step 1: fetch homepage via MCP |
| `output_keys` | StrEnum | `conference_agent/schemas/output_keys.py:4` | Session state keys for pipeline |
| `test` | async func | `conference_agent/tools/scrapling_tool.py:15` | Manual scraping test runner |

## CONVENTIONS
- **Settings hierarchy**: `init_settings > env_settings > YAML > dotenv` (explicit in `SystemSettings.settings_customise_sources`).
- **Schema enrichment order**: homepage → sub-pages (speakers, venue, registration) → geocoding enrichment for `travel_hours` / `is_local` / `is_usa`.
- **LLM temperature by role**: orchestrator 0.2, extraction 0.1, validation 0.1, relevance_filter 0.0.
- **Prompt placeholders**: All extraction prompts use `{markdown}` as the single template variable.
- **Pydantic models for everything**: Inputs, outputs, and config are all strictly typed Pydantic models.

## ANTI-PATTERNS (THIS PROJECT)
- **DO NOT hardcode config values** — always use `settings` singleton from `config.py`.
- **DO NOT skip `speakers_confirmed` check** — an empty speaker list is different from unconfirmed speakers.
- **DO NOT geocode before confirming speakers exist** — `travel_hours`, `is_local`, `is_usa` are blocked until geocoding step.
- **NEVER return markdown backticks in LLM prompts** — extraction prompts explicitly demand raw JSON only.
- **NEVER store secrets in settings.yaml** — use environment variables (`.env` support exists).

## UNIQUE STYLES
- **MCP-first tooling**: Web scraping is an external MCP server (`scrapling_mcp_url`), not a local dependency. Agent uses `McpToolset` + `StreamableHTTPConnectionParams`.
- **Prompt-driven extraction**: No HTML parsers — all structured data extraction is LLM-prompt-based with strict JSON schemas.
- **Schema-first validation**: Validation rules are Pydantic models (`ValidationResult`) with literal enums (`"now" | "future" | "reject"`).

## COMMANDS
```bash
# Run agent
python -m conference_agent

# Test scraping tool
python conference_agent/tools/scrapling_tool.py

# Test step 1 agent
uv run python conference_agent/tests/test_step1_scrape_homepage.py

# Start MCP server (Docker)
docker run -d -p 8016:8016 --name scrapling-mcp pyd4vinci/scrapling:latest mcp --http --port 8016

# Install dependencies
uv pip install -e ".[extensions]"
```

## NOTES
- `main.py` is currently a stub (`print("Hello from conference-discovery!")`). Real entry point is `conference_agent/` package.
- `requirements.txt` is empty — all deps declared in `pyproject.toml`.
- Scrapling MCP server must be running locally at `http://localhost:8016/mcp`.
  Use `--http --port 8016` flags; default `stdio` transport won't work with ADK.
- `output/` contains manual test artifacts, not committed production output.
- Tests live in `conference_agent/tests/` (root `tests/` removed).
- `database/` is reserved for future persistence layer.
