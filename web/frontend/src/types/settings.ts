/** Settings types matching SettingsResponse from web/schemas.py */

export interface DiscoverySources {
  exa: boolean;
  directories: boolean;
  org_websites: boolean;
}

export interface DiscoverySettings {
  topic: string;
  months_ahead: number;
  sources: DiscoverySources;
}

export interface ExaSettings {
  num_results: number;
  pages_per_query: number;
}

export interface DateWindow {
  min_days: number;
  max_days: number;
}

export interface ValidationSettings {
  min_speakers: number;
  min_non_local: number;
  min_travel_hours: number;
  date_window: DateWindow;
}

export interface OutputSettings {
  excel_path: string;
  notify_email: string;
}

export interface LLMModelConfig {
  model: string;
  temperature: number;
}

export interface LlmSettings {
  orchestrator: LLMModelConfig;
  extraction: LLMModelConfig;
  discovery: LLMModelConfig;
  validation: LLMModelConfig;
  relevance_filter: LLMModelConfig;
}

export interface Settings {
  topics: Record<string, string>;
  discovery: DiscoverySettings;
  exa: ExaSettings;
  validation: ValidationSettings;
  output: OutputSettings;
  llm: LlmSettings;
  scrapling_mcp_url: string;
  debug: boolean;
}
