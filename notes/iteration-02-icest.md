# QA Iteration 2: ICEST 2026

**URL:** https://icest.org/
**Type:** Single-page academic conference site (no sub-page navigation)

## Manual Extraction

| Field | Value |
|-------|-------|
| Conference Name | 2026 17th International Conference on Environmental Science and Technology (ICEST 2026) |
| Dates | December 4-6, 2026 |
| Venue | Xiamen, China |
| Organizer | International Society for Environmental Information Sciences |
| Co-organizer | Jimei University, United Nations Development Programme |
| Field | Environmental Science and Technology |
| Publication | EI Compendex, Scopus |

**Sub-pages:** None — this is a single-page site. All info (submission, registration, dates) is on one page.

## Pipeline Run

Completed in 103.4s. All 7 steps succeeded.

### Comparison

| Field | Pipeline | Manual | Match? |
|-------|----------|--------|--------|
| Conference Name | 17th ICEST 2026 | 2026 17th ICEST 2026 | **YES** |
| Dates | 2026-12-04 -> 2026-12-06 | December 4-6, 2026 | **YES** |
| Industry | environmental science and technology | Environmental Science and Technology | **YES** |
| City | Xiamen | Xiamen | **YES** |
| Country | China | China | **YES** |
| Venue Name | null (no specific building) | None specified | **Correct** |
| Speakers | 0 (no speakers page) | Not on site | **Correct** |
| Registration URL | https://www.zmeeting.org/register/ICEST2026 | Found on homepage | **YES** |

### Notes
- Single-page site — no separate sub-pages for speakers/venue (expected)
- Registration URL discovered correctly from the Registration section on the homepage
- Pipeline extracted city/country from homepage content (correct)
- No venue name expected (conference location is "Xiamen, China" — a city, not a specific building)
- Sub-pages scraped: 511 chars (only registration page)
- **Score: ~95%**

