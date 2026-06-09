# QA Iteration 1: AIME 2026

**URL:** https://aime26.aimedicine.info/
**Type:** Professional academic conference site (WordPress-based)

## Manual Extraction (via Playwright)

| Field | Value |
|-------|-------|
| Conference Name | International Conference on Artificial Intelligence in Medicine (AIME 2026) |
| Dates | July 7-10, 2026 |
| City/Country | Ottawa, Canada |
| Venue | University of Ottawa |
| Organizer | Society for Artificial Intelligence in Medicine |
| Field | Artificial Intelligence in Medicine, Healthcare AI |

**Sub-pages found in nav:**
- Registration: https://aime26.aimedicine.info/registration/
- Organization, Venue, Submissions, Program, Travel Info, Sponsors (dropdown menus with # hrefs)

**Nav items with actual URLs:** Home, Registration (direct URL)
**Nav items with # hrefs:** Organization, Venue, Submissions, Program, Travel Info, Sponsors

## Pipeline Run

Completed in 288.2s. All 7 steps succeeded.

### Comparison

| Field | Pipeline | Manual | Match? |
|-------|----------|--------|--------|
| Conference Name | AIME 2026: International Conference on AI in Medicine | International Conference on AI in Medicine (AIME 2026) | **YES** |
| Dates | 2026-07-07 -> 2026-07-10 | July 7-10, 2026 | **YES** |
| Industry | medicine | Artificial Intelligence in Medicine | **Acceptable** |
| City | Ottawa | Ottawa | **YES** |
| Country | Canada | Canada | **YES** |
| Venue | Learning Crossroads (CRX) and Desmarais Hall (DMS) | University of Ottawa (vague) | **BETTER** than manual |
| Speakers | 0 (not confirmed) | Not on homepage | **Correct** |
| Registration URL | https://aime26.aimedicine.info/registration/ | Same | **YES** |
| Venue URL | https://aime26.aimedicine.info/venue/ | Not visible on homepage | **FOUND** |

### Notes
- Venue was MORE specific than manual extraction (the pipeline found specific building names from the venue sub-page)
- Speakers page exists but has no confirmed speakers yet (correct behavior)
- Pipeline discovered sub-page URLs that were hidden behind JavaScript dropdown menus
- Sub-pages scraped: 10810 chars (good content)
- Homepage scraped: 4479 chars
- **Score: ~95%**

