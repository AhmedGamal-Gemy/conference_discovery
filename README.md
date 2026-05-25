# Conference Discovery

Conference discovery agent that scrapes conference websites, extracts structured data via LLM prompts, and validates conferences against configurable criteria (speaker count, travel time, dates). Built with Google ADK + Pydantic.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management
- Docker (for Scrapling MCP server)
- Mistral API key

## Quick Start

### 1. Start the Scrapling MCP Server

The scrapling MCP server must be running before any agent or test can fetch web pages. Note that scrapling defaults to `stdio` transport; you must pass `--http` to enable the HTTP transport used by ADK:

```bash
docker run -d -p 8016:8016 --name scrapling-mcp pyd4vinci/scrapling:latest mcp --http --port 8016
```

Verify it's up (expect a JSON-RPC error about `text/event-stream` — this confirms the server is listening):
```bash
curl http://localhost:8016/mcp
# Response: {"jsonrpc":"2.0","id":"server-error",..."Not Acceptable: Client must accept text/event-stream"}
```

To stop:
```bash
docker stop scrapling-mcp
```

To restart:
```bash
docker start scrapling-mcp
```

### 2. Install Dependencies

```bash
uv pip install -e ".[extensions]"
```

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
MISTRAL_API_KEY=your-mistral-api-key-here
```

Or set it directly:
```bash
# Windows PowerShell
$env:MISTRAL_API_KEY="your-mistral-api-key-here"

# Linux/Mac
export MISTRAL_API_KEY=your-mistral-api-key-here
```

### 4. Run Tests

```bash
# Test step 1: scrape homepage
uv run python conference_agent/tests/test_step1_scrape_homepage.py

# Test step 2: extract structured data from markdown
uv run python conference_agent/tests/test_step2_extract_homepage.py

# Test full pipeline (orchestrator: step1 -> delay -> step2)
uv run python conference_agent/tests/test_orchestrator.py
```

## Project Structure

```
conference_discovery/
├── conference_agent/         # Core agent package
│   ├── steps/                # ADK step agents (orchestration pipeline)
│   │   ├── step1_scrape_homepage.py
│   │   ├── step2_extract_homepage.py
│   │   └── step_rate_limit_delay.py
│   ├── tests/                # Test suite
│   │   ├── test_step1_scrape_homepage.py
│   │   ├── test_step2_extract_homepage.py
│   │   └── test_orchestrator.py
│   ├── agent.py              # Root ADK orchestrator agent
│   ├── config.py             # SystemSettings (YAML + env + init priority)
│   ├── orchestrator.py       # SequentialAgent chaining step1 -> delay -> step2
│   ├── prompts/              # LLM extraction prompts
│   │   └── extraction.py     # Homepage, speakers, venue, registration prompts
│   ├── schemas/              # Pydantic data models
│   │   ├── conference.py     # Top-level composed model
│   │   ├── homepage.py       # Homepage extraction target
│   │   ├── output_keys.py    # Pipeline state key enum
│   │   ├── speaker.py        # Speakers page extraction target
│   │   ├── venue.py          # Venue page extraction target
│   │   ├── registration.py   # Registration page extraction target
│   │   └── validation.py     # Pass/fail with rejection reason
│   └── tools/                # MCP toolsets + utilities
│       ├── scrapling_tool.py # MCP client for stealthy_fetch
│       ├── intermediate_output.py # Persist state to output/intermediate/
│       ├── discovery_tool.py # Exa search + relevance filter
│       ├── exa_tool.py       # Exa API wrapper
│       ├── query_generator.py
│       └── relevance_filter.py
├── config/
│   └── settings.yaml         # YAML settings (topic, thresholds, LLM temps, MCP URL)
├── database/                 # (empty — TBD persistence layer)
├── notes/                    # Research notes (schema-viability.md)
├── output/                   # Scraping results + intermediate pipeline snapshots
│   └── intermediate/         # Session state saved as .md / .json
├── main.py                   # Entry point (stub)
└── pyproject.toml            # Python dependencies
```

## Configuration

Edit `config/settings.yaml` to adjust:
- **Discovery topic**: `discovery.topic` (default: `"medical"`)
- **Validation thresholds**: `validation.min_speakers`, `min_non_local`, `min_travel_hours`, `date_window`
- **LLM models**: `llm.*.model` and temperatures per role
- **MCP server URL**: `scrapling_mcp_url` (default: `http://localhost:8016/mcp`)

## Commands

```bash
# Run agent
python -m conference_agent

# Test scraping tool directly
uv run python conference_agent/tools/scrapling_tool.py

# Test individual steps
uv run python conference_agent/tests/test_step1_scrape_homepage.py
uv run python conference_agent/tests/test_step2_extract_homepage.py

# Test full pipeline
uv run python conference_agent/tests/test_orchestrator.py

# Install dependencies
uv pip install -e ".[extensions]"
```
