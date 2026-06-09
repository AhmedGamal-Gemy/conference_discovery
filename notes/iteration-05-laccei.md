# QA Iteration 5: LACCEI 2026

**URL:** https://laccei.org/laccei2026/
**Type:** Multi-conference engineering event with sub-pages (WordPress)

## Manual Extraction

| Field | Value |
|-------|-------|
| Conference Name | 24th LACCEI International Multi-Conference for Engineering, Education and Technology |
| Dates | July 15-17, 2026 |
| Venue | InterContinental Santiago, Chile (Hybrid) |
| Organizer | LACCEI, FAU, OAS |
| Field | Engineering, Education, Technology |

**Sub-pages found:**
- Venue: https://laccei.org/laccei2026/venue/
- Registration: https://laccei.org/laccei2026/registration/
- Program: https://laccei.org/laccei2026/program/
- Sponsors: https://laccei.org/laccei2026/sponsors/
- Authors: https://laccei.org/laccei2026/authors/
- Students: https://laccei.org/laccei2026/student/

**Registration:** External system at conftool.pro

## Pipeline Run

Completed in 127.2s. All 7 steps succeeded.

### Comparison

| Field | Pipeline | Manual | Match? |
|-------|----------|--------|--------|
| Conference Name | 24th LACCEI Multi-Conference | Same | **YES** |
| Dates | 2026-07-15 -> 2026-07-17 | July 15-17, 2026 | **YES** |
| Industry | engineering and technology | Engineering, Education, Technology | **YES** |
| Speakers | 0 (no speakers page) | Not listed | **Correct** |
| Venue | InterContinental Santiago (full address) | InterContinental Santiago | **YES** |
| City | Santiago | Santiago | **YES** |
| Country | Chile | Chile | **YES** |
| Venue URL | /venue/ | Same | **YES** |
| Registration URL | /registration/ | Conftool external link | **YES** |

### Notes
- Venue found correctly with full address (Avenida Vitacura 2885 Las Condes)
- InterContinental Santiago correctly identified as hotel (is_hotel: True)
- No speakers page exists on this site (correct behavior)
- Registration URL points to the LACCEI registration info page
- All sub-page URLs correctly resolved (URL fix worked)
- **Score: ~98%**

