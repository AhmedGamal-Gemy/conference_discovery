from typing import Tuple, Type
from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    YamlConfigSettingsSource,
)

from pathlib import Path

_ROOT = Path(__file__).parent.parent  # conference_agent/ → project root

# ── Nested models ──────────────────────────────────────────────────


class DiscoverySources(BaseModel):
    exa: bool = True
    directories: bool = False
    org_websites: bool = False


class DiscoveryConfig(BaseModel):
    topic: str = "medical"
    months_ahead: int = 3
    sources: DiscoverySources = DiscoverySources()


class ExaConfig(BaseModel):
    num_results: int = 10
    pages_per_query: int = 2


class DateWindow(BaseModel):
    min_days: int = 30
    max_days: int = 90


class ValidationConfig(BaseModel):
    min_speakers: int = 5
    min_non_local: int = 5
    min_travel_hours: int = 4
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

# Run the code
if __name__ == "__main__":
    # You don't need to pass the dict manually anymore!
    # BaseSettings automatically finds and loads the YAML file on instantiation.
    print(settings.discovery.topic)