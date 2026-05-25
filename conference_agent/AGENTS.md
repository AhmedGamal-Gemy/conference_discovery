# conference_agent/ KNOWLEDGE BASE

**Scope:** Core agent package — ADK orchestration, configuration, data schemas, extraction prompts, and MCP tools.

## OVERVIEW
Google ADK-based agent package that discovers and validates conferences via LLM-driven web scraping.

## WHERE TO LOOK
| Task | File | Notes |
|------|------|-------|
| Change root LLM agent | `agent.py` | `root_agent` uses `LiteLlm("mistral/mistral-large-latest")` |
| Add/modify config | `config.py` | `SystemSettings` loads `config/settings.yaml` via pydantic-settings |
| Add extraction prompt | `prompts/extraction.py` | Prompts demand raw JSON, no markdown backticks |
| Add data model | `schemas/*.py` | All Pydantic; import in `conference.py` for top-level composition |
| Fix scraping | `tools/scrapling_tool.py` | MCP toolset for `stealthy_fetch` |
| Wire new schema into Conference | `schemas/conference.py` | Composes `HomepageData + VenueData + RegistrationData + list[Speaker]` |
| Add step agent | `steps/*.py` | ADK `LlmAgent` with `output_key` for pipeline state |
| Add test | `tests/*.py` | Runner-based tests for step agents |
| Add state key | `schemas/output_keys.py` | `StrEnum` used by `output_key` across steps |
| Change orchestrator | `orchestrator.py` | `SequentialAgent` chains step1 → delay → step2 |
| Add delay between steps | `steps/step_rate_limit_delay.py` | Custom `BaseAgent` that sleeps |
| Save intermediate output | `tools/intermediate_output.py` | Writes state to `output/intermediate/` |

## CONVENTIONS
- Every schema lives in its own file under `schemas/`.
- `__init__.py` only exports `agent` — no wildcard imports.
- Prompts are plain triple-quoted strings with a single `{markdown}` or `{state.url}` placeholder.
- MCP toolsets are instantiated at module level with config from `settings` singleton.
- Step agents go in `steps/` and declare `output_key` for downstream consumption.
- Tests go in `tests/` and use `Runner` + `InMemorySessionService` for ADK integration testing.

## ANTI-PATTERNS
- **DO NOT import `settings` at module level in schemas** — schemas are pure Pydantic, no side effects.
- **DO NOT add business logic to schema files** — keep them declarative.
- **NEVER commit MCP server credentials** — URL comes from `settings.scrapling_mcp_url` (env or YAML).
