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
| `DiscoveredLinksData` | `discovered_links.py` | (discover_links step) | `links: list[DiscoveredLink]` (url, link_text, category) |
| `ValidationResult` | `validation.py` | (validation layer) | `passed`, `failed_condition`, `rejection_reason`, `date_bucket` |
| `Conference` | `conference.py` | (composed) | Aggregates all sub-models + derived counters |
| `output_keys` | `output_keys.py` | (pipeline contract) | `StrEnum` — lowercase via `auto()` |

## OUTPUT KEYS
Defined in `output_keys.py` — all lowercase via `StrEnum.auto()`:
- `URL` — input target URL (`"url"`)
- `HOMEPAGE_MARKDOWN` — scraped homepage content (`"homepage_markdown"`)
- `HOMEPAGE_DATA` — extracted conference data
- `DISCOVERED_LINKS` — classified links from homepage
- `PROBED_LINKS` — results from URL path probing
- `SUB_PAGES_URLS` — merged speaker/venue/registration URLs
- `SCRAPED_SUB_PAGES` — scraped sub-page markdown
- `SPEAKERS_DATA` — extracted speakers data
- `VENUE_DATA` — extracted venue data
- `REGISTRATION_DATA` — extracted registration data

## DISCOVERED LINK CATEGORIES
The `DiscoveredLink` model uses a `Literal` type for category:
- `speakers` — keynote, invited talks, speakers list
- `venue` — location, hotels, travel, accommodation
- `registration` — tickets, fees, payment, attending
- `schedule` — program, agenda, timetable, sessions
- `blog` — blog posts, articles
- `news` — announcements, press releases, updates
- `other` — sponsors, FAQ, code of conduct, etc.

## CONVENTIONS
- All fields are `Optional[...]` except booleans and IDs — LLM extraction may miss fields.
- Derived counters (`total_speakers`, `non_local_count`, `non_usa_count`) live on `Conference`, never on sub-models.
- Geocoding-enriched fields (`travel_hours`, `is_local`, `is_usa`) are optional on `Speaker` — populated post-scrape.
- `date_bucket` is a `Literal["now", "future", "reject"]` — used for scheduling/prioritization.
- SubPages (from `homepage.py`) has 3 fields: `speakers`, `venue`, `registration` (all `Optional[str]`).

## ANTI-PATTERNS
- **DO NOT add extraction logic to models** — keep models pure; prompts live in `../prompts/`.
- **DO NOT make booleans optional** — use explicit defaults (`False`) so LLM always has a value to override.
- **NEVER add fields without updating the corresponding prompt** — schema and prompt must stay in sync.
- **output_schema stores as dict in state** — `output_key` on sub-agents saves as plain dict, not Pydantic model instance. Validate with `Model.model_validate(state[key])` when reading back.
- **DO NOT set SubPages fields to empty string** — use `None` to indicate "not found/not applicable".
