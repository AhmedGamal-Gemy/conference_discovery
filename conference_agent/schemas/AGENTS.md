# schemas/ KNOWLEDGE BASE

**Scope:** Pydantic data models — the contract between LLM extraction prompts and downstream validation.

## OVERVIEW
Strictly typed Pydantic models representing conference data. Each model maps to one extraction prompt output.

## WHERE TO LOOK
| Model | File | Maps to Prompt | Key Fields |
|-------|------|----------------|------------|
| `HomepageData` | `homepage.py` | `HOMEPAGE_EXTRACTION_PROMPT` | `conference_name`, `date_start`, `date_end`, `industry`, `sub_pages` |
| `SpeakersData` | `speaker.py` | `SPEAKERS_EXTRACTION_PROMPT` | `speakers[]`, `speakers_confirmed` |
| `VenueData` | `venue.py` | `VENUE_EXTRACTION_PROMPT` | `venue_name`, `venue_address`, `city`, `country`, `is_hotel` |
| `RegistrationData` | `registration.py` | `REGISTRATION_EXTRACTION_PROMPT` | `covers_accommodation` |
| `ValidationResult` | `validation.py` | (validation layer) | `passed`, `failed_condition`, `rejection_reason`, `date_bucket` |
| `Conference` | `conference.py` | (composed) | Aggregates all sub-models + derived counters |
| `output_keys` | `output_keys.py` | (pipeline contract) | `StrEnum` — `URL`, `HOMEPAGE_MARKDOWN`, etc. |

## CONVENTIONS
- All fields are `Optional[...]` except booleans and IDs — LLM extraction may miss fields.
- Derived counters (`total_speakers`, `non_local_count`, `non_usa_count`) live on `Conference`, never on sub-models.
- Geocoding-enriched fields (`travel_hours`, `is_local`, `is_usa`) are optional on `Speaker` — populated post-scrape.
- `date_bucket` is a `Literal["now", "future", "reject"]` — used for scheduling/prioritization.

## ANTI-PATTERNS
- **DO NOT add extraction logic to models** — keep models pure; prompts live in `../prompts/`.
- **DO NOT make booleans optional** — use explicit defaults (`False`) so LLM always has a value to override.
- **NEVER add fields without updating the corresponding prompt** — schema and prompt must stay in sync.
