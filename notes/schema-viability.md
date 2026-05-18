# Schema Viability

## Test 1 — ICENH-26

Source: `https://after.org.in/event/index.php?id=100947439`  
Scraped pages: homepage, venue, registration, speakers

### Fillable (no extra work)

| Model | Field | Source |
|---|---|---|
| `Conference` | `conference_id` | → `"ICENH-26"` from homepage title |
| `Conference` | `website_url` | → `"https://after.org.in"` |
| `Conference` | `speakers_page_url` | → speakers page URL |
| `Conference` | `total_speakers` | → count from speakers page |
| `HomepageData` | `conference_name` | ✅ |
| `HomepageData` | `date_start` | ✅ |
| `HomepageData` | `date_end` | ✅ |
| `HomepageData` | `industry` | ✅ |
| `HomepageData` | `sub_pages.*` | ✅ (needs `/event/` prefix fix) |
| `VenueData` | all 5 fields | ✅ venue page |
| `RegistrationData` | `covers_accommodation` | ✅ inferred from pricing |
| `Speaker` | `name` | ✅ |
| `Speaker` | `title` | ✅ (usually) |
| `Speaker` | `affiliation` | ✅ (usually) |
| `Speaker` | `country` | ✅ (often explicit) |
| `Speaker` | `is_scientific` | ✅ LLM judgment call |

### Blocked (needs Google Maps geocoding enrichment)

| Model | Field | Reason |
|---|---|---|
| `Speaker` | `travel_hours` | needs distance from affiliation city → Berlin |
| `Speaker` | `is_local` | needs geocoding + radius check |
| `Speaker` | `is_usa` | needs country normalization |
| `Conference` | `non_local_count` | blocked by `is_local` |
| `Conference` | `non_usa_count` | blocked by `is_usa` |

### Edge case

`speakers` lists **past** conference speakers, not ICENH-26's speakers.
Since the conference is Dec 2026, the actual speaker list probably doesn't exist yet.

---

## Test 2 — ICAASS

Source: `https://academicsconference.com/Conference/81158/ICAASS/`  
Scraped pages: homepage, keynote, venue, registration

### Fillable

| Model | Field | Source |
|---|---|---|
| `Conference` | `conference_id` | `"ICAASS"` |
| `HomepageData` | all 5 fields | ✅ homepage |
| `VenueData` | all 5 fields | ✅ venue page (`is_hotel: True`) |
| `RegistrationData` | `covers_accommodation` | ✅ inferred False |

### Speakers

```
speakers: []                          ← keynote page says "Will Be Updated Soon"
speakers_confirmed: False             ← correctly False
```

`total_speakers`, `non_local_count`, `non_usa_count` all = 0 — technically correct but meaningless when list is empty.

### Blocked

Same 3 geocoding fields as ICENH-26 (travel_hours, is_local, is_usa) — applies whenever speakers exist.

---

## Cross-test observations

### 1. `speakers_confirmed: bool` passes both tests
- ICENH-26: had past speakers but no confirmed current ones → `False` ✅
- ICAASS: literally zero speakers → `False` ✅

### 2. Sub-page URL patterns vary by site
- AFTER uses query params:     `venue.php?id=100947439`
- AcademicsConference uses paths: `Conference/81158/ICAASS/venue`
- Both resolve correctly from the scraped page URL as base

### 3. `total_speakers=0` + counters = 0 is noise
When no speakers exist, the three integer fields are dead weight. They only carry meaning when `speakers` is populated.

### 4. `covers_accommodation` weak inference
Both times set to `False` because registration fees don't cover hotels. But if a fee is high enough to include accommodation, there's no explicit boolean on the page — the inference is price-based and brittle.

### 5. Data present on pages but outside the schema
- Deadlines (always on homepage or reg page)
- Session tracks (ICENH-26 had 5)
- Registration fee tables (both conferences had them)
- Conference format (hybrid/in-person/virtual)
- Contact email / phone
