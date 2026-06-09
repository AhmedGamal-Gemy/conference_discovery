# QA Iteration 3: ISITIA 2026

**URL:** https://isitia.its.ac.id/conf/isitia/main/
**Type:** WordPress-based IEEE conference site with sidebar

## Manual Extraction

| Field | Value |
|-------|-------|
| Conference Name | 27th International Seminar on Intelligent Technology and Its Applications (ISITIA) 2026 |
| Dates | 22-24 July 2026 |
| Venue | Hybrid: Kuta, Bali, INDONESIA (Onsite) + Online |
| Organizer | Dept of Electrical Engineering, ITS, Indonesia |
| Field | Intelligent Technology, Engineering |
| Publication | IEEE Xplore, Scopus |

**Keynote Speakers (listed on homepage):**
1. Prof. Kenichi Okada — Institute of Science Tokyo, Japan
2. Assoc. Prof. Astria Nur Irfansyah — ITS, Indonesia
3. Assoc. Prof. Anis Salwa Mohd Khairuddin — Universiti Malaya, Malaysia
4. Dr. Ngurah Indra ER — Universitas Udayana

**Keynote speakers page:** https://elib.its.ac.id/conf/isitia/main/keynote-speakers/
**Registration:** Not directly linked on homepage (likely via IEEE)

## Pipeline Run

Completed in 182.2s. All 7 steps succeeded.

### Comparison

| Field | Pipeline | Manual | Match? |
|-------|----------|--------|--------|
| Conference Name | 27th ISITIA 2026 | Same | **YES** |
| Dates | 2026-07-22 -> 2026-07-24 | 22-24 July 2026 | **YES** |
| Industry | engineering | Intelligent Technology, Engineering | **Acceptable** |
| Speakers | **4** (confirmed) | 4 keynote speakers | **YES** |
| Speaker names | Kenichi Okada, Astria Nur Irfansyah, Anis Salwa Khairuddin, Ngurah Indra ER | Same | **YES** |
| Venue | **Bali Dynasty Resort** (with full address) | "Kuta, Bali" (vague) | **BETTER** |
| City | Badung | Kuta, Bali | **More precise** |
| Country | Indonesia | Indonesia | **YES** |
| Registration URL | /registration/ | Not found manually | **FOUND** |
| Speakers URL | /keynote-speakers/ | Same | **YES** |

### Key Observations
- **Best result yet!** Pipeline found full venue details (Bali Dynasty Resort, full address) that I missed manually
- All 4 keynote speakers correctly extracted and marked as confirmed
- Pipeline discovered sub-page URLs that were hidden in navigation
- URL resolution fix worked correctly for this nested path (`/conf/isitia/main/`)
- **Score: ~98%**

