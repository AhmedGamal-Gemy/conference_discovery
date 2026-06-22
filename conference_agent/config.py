import litellm

# Client-side retries disabled — the LiteLLM proxy handles rate limiting.
litellm.num_retries = 0

from typing import Optional, Tuple, Type
from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    YamlConfigSettingsSource,
)

from pathlib import Path
from dotenv import load_dotenv

_ROOT = Path(__file__).parent.parent  # conference_agent/ → project root
load_dotenv(_ROOT / "conference_agent" / ".env")  # Must load .env BEFORE proxy key resolution

# ── Nested models ──────────────────────────────────────────────────


class DiscoverySources(BaseModel):
    exa: bool = True
    directories: bool = False
    org_websites: bool = False


class DiscoveryConfig(BaseModel):
    topic: str = "medical"
    months_ahead: int = 3
    query_templates: list[str] = []  # Empty = use defaults from query_generator
    subfields: list[str] = []  # Topic-specific sub-categories for subfield queries (empty = no subfield queries)
    sources: DiscoverySources = DiscoverySources()


class ExaConfig(BaseModel):
    num_results: int = 10
    pages_per_query: int = 2
    type: str = "neural"           # Exa search type — neural (semantic) handles query optimization internally
    text_max_chars: int = 1000     # Richer snippets for relevance filter (was hardcoded 500)
    include_domains: list[str] = []   # Restrict search to these domains (empty = no restriction)
    exclude_domains: list[str] = []   # Exclude these domains from search results


class DateWindow(BaseModel):
    min_days: int = 30
    max_days: int = 90


class LogConfig(BaseModel):
    file: str = "logs/pipeline.log"
    max_bytes: int = 10_485_760  # 10 MB
    backup_count: int = 3


class ValidationConfig(BaseModel):
    min_speakers: int = 5
    min_non_local: Optional[int] = None
    min_travel_hours: Optional[int] = None
    min_non_usa: Optional[int] = None
    date_window: DateWindow = DateWindow()


class OutputConfig(BaseModel):
    excel_path: str = "./output/conferences.xlsx"
    notify_email: str = ""


class LLMModelConfig(BaseModel):
    model: str = "mistral/mistral-small-latest"
    temperature: float = 0.1


class LLMConfig(BaseModel):
    orchestrator: LLMModelConfig = LLMModelConfig(temperature=0.2)
    discovery: LLMModelConfig = LLMModelConfig(temperature=0.2)
    extraction: LLMModelConfig = LLMModelConfig(temperature=0.1)
    validation: LLMModelConfig = LLMModelConfig(temperature=0.1)
    relevance_filter: LLMModelConfig = LLMModelConfig(temperature=0.0)

class SystemSettings(BaseSettings):

    discovery: DiscoveryConfig
    exa: ExaConfig
    validation: ValidationConfig
    output: OutputConfig
    llm: LLMConfig
    logging: LogConfig
    scrapling_mcp_url:str
    debug: bool

    # Point to your YAML file here
    model_config = SettingsConfigDict(yaml_file= str(_ROOT / "config" / "settings.yaml"))

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            # 1. Init settings (arguments passed directly to the class) take highest priority
            init_settings,
            # 2. Environment variables take next priority
            env_settings,
            # 3. YAML file takes next priority
            YamlConfigSettingsSource(settings_cls),
            # 4. .env files take lowest priority (if you use them)
            dotenv_settings,
        )

settings = SystemSettings() # type: ignore

# ── LiteLLM proxy config (after settings so .env vars are loaded) ──────
import os as _os
# Official ADK+LiteLLM proxy pattern:
# https://docs.litellm.ai/docs/tutorials/google_adk#5-using-litellm-proxy-with-adk
_litellm_proxy_key = _os.environ.get(
    "LITELLM_PROXY_API_KEY",
    "sk-GE_MBZsUSFrR3FQ86lZ8hg",
)
_os.environ["LITELLM_PROXY_API_KEY"] = _litellm_proxy_key
_os.environ.setdefault("LITELLM_PROXY_API_BASE", "http://localhost:4000")
litellm.use_litellm_proxy = True  # Routes all LLM calls through the proxy

# Run the code
if __name__ == "__main__":
    # You don't need to pass the dict manually anymore!
    # BaseSettings automatically finds and loads the YAML file on instantiation.
    print(settings.discovery.topic)

