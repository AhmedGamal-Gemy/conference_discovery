# QA Iteration 4: POCER 2026

**URL:** https://www.nottingham.edu.my/Conferences/POCER-2026/index.aspx
**Type:** University-hosted, .NET ASPX single-page conference site

## Manual Extraction

| Field | Value |
|-------|-------|
| Conference Name | 8th International Conference and Postgraduate Colloquium of Environmental Research (POCER 2026) |
| Dates | 8-9 July 2026 |
| Venue | University of Nottingham Malaysia |
| Organizer | University of Nottingham Malaysia |
| Field | Environmental Research |
| Publication | IOP Conference Series (Scopus) |
| Theme | Weaving a Resilient and Sustainable Future |

**Keynote Speakers (listed on page):**
1. Ir Dr Norshah Hafeez Shuaib — Executive Director & CTO, MTC Group
2. Ar (Dr) Serina Hijjas — Principal Director, Hijjas Kasturi Associates
3. Basil Theckumpurath, P.E. — Head of Country, Genesis Malaysia
4. Professor Jonathan Wong — Dongguan University of Technology

**Plenary Speakers:**
1. Prof Matthew Ashfold — University of Nottingham Malaysia
2. Dr Subarna Sivapalan — University of Nottingham Malaysia
3. Prof Ir Dr Denny Ng Kok Sum — Sunway University
4. Dr Fadlilatul Taufany — ITS Indonesia
5. Dr Saffron Bryant — RMIT Australia
6. Dr Rosazlin Abdullah — Universiti Malaya

**Registration:** Detailed pricing table (RM/USD), on-campus accommodation available

## Pipeline Run

Completed in 164.7s. All 7 steps succeeded.

### Comparison

| Field | Pipeline | Manual | Match? |
|-------|----------|--------|--------|
| Conference Name | 8th POCER 2026 | Same | **YES** |
| Dates | 2026-07-08 -> 2026-07-09 | 8-9 July 2026 | **YES** |
| Industry | environmental science | Environmental Research | **Acceptable** |
| Speakers | 0 (no sub-page found) | 4 keynote + 6 plenary on homepage | **NO** |
| City | Semenyih | Semenyih, Malaysia | **YES** |
| Country | Malaysia | Malaysia | **YES** |
| Venue Name | null | University of Nottingham Malaysia | **NO** |
| Registration URL | External Forms URL | Same | **YES** |

### Notes
- Single-page site: all content (speakers, venue) is on the homepage, not separate sub-pages
- Pipeline found 14,720 chars of homepage content (most so far) but couldn't extract speakers because they're labeled "Keynote speakers" and "Plenary speakers" on the same page, not a dedicated "/speakers/" sub-page
- Registration URL correctly extracted (Microsoft Forms link)
- Venue URL incorrectly found the shuttle-bus page instead of the venue page
- **Limitation identified**: Pipeline relies on sub-page discovery for speakers/venue extraction. Single-page sites lose this data.
- **Score: ~70%** (misses speakers and venue detail)

