# Pipeline vs Manual Extraction Comparison

**URL:** https://scholarsforum.net/event/index.php?id=100442671
**Pipeline runs:**
- Run 1: 118.4s (failed due to URL resolution bug)
- Run 2: 176.1s (completed all 7 steps, URL fix applied)

---

## Comparison Table

| Field | Pipeline | Manual (via Playwright) | Match? |
|-------|----------|------------------------|--------|
| Conference Name | International Conference on Ocean-Borne Diseases and Biological Contaminants | Same | **YES** |
| Date Start | 2026-06-19 | Same | **YES** |
| Date End | 2026-06-20 | Same | **YES** |
| Industry | environmental science | Ocean-Borne Diseases, Biological Contaminants, Oceanography, Biology, Environmental Sustainability | **NO** (simplified) |
| Venue Name | Hotel Sofitel Munich Bayerpost | Same | **YES** |
| Venue Address | Bayerstrabe 12, 80335 Munchen, Germany | Same | **YES** |
| City | Munich | Same | **YES** |
| Country | Germany | Same | **YES** |
| Speakers Count | **0** | 9 (past speakers) | **Partial** (correctly identified as past speakers) |
| Speakers Confirmed | False | False (past speakers only) | **YES** |
| Speakers Page URL | https://scholarsforum.net/event/test_pastspeakers.php?id=100442671 | Same | **YES** |
| Venue Page URL | https://scholarsforum.net/event/venue.php?id=100442671 | Same | **YES** |
| Registration Page URL | https://scholarsforum.net/payment/list_index.php?id=100442671 | Same | **YES** |
| Covers Accommodation | False | False (not mentioned) | **YES** |

---

## What Was Found (Pipeline)

1. **Conference Name**: Correctly extracted
2. **Dates**: Correctly extracted
3. **Industry**: Simplified to "environmental science" (lost granularity)
4. **Sub-page URLs**: Correctly discovered and classified
5. **Venue**: Correctly extracted (name, address, city, country, is_hotel)
6. **Registration**: Covers accommodation: false
7. **Speakers**: Correctly identified as past speakers (not confirmed), returned empty list

---

## What Was NOT Found (Pipeline)

1. **Speakers list**: Empty list (correctly identified as past speakers, not confirmed)
2. **Registration pricing**: Not captured (USD 409-1900 pricing table)
3. **Session tracks**: Not captured
4. **Conference schedule**: Not captured
5. **SDGs alignment**: Not captured
6. **Industry granularity**: Simplified to "environmental science"

---

## Root Cause (Fixed)

**Issue 1: URL resolution bug** (FIXED)
- The LLM was resolving relative URLs incorrectly, stripping the `/event/` directory
- **Fix**: Improved prompt + added Python `urljoin` post-processing in `run_pipeline.py`

**Issue 2: Industry simplification** (NOT FIXED)
- LLM simplified "Ocean-Borne Diseases, Biological Contaminants, Oceanography, Biology, Environmental Sustainability" to "environmental science"
- **Fix needed**: Improve prompt to preserve full field names

---

## Summary

| Metric | Score |
|--------|-------|
| Homepage data | **80%** (name, dates correct; industry oversimplified) |
| Sub-page URL discovery | **100%** |
| Sub-page scraping | **100%** (after URL fix) |
| Sub-page extraction | **80%** (venue correct; speakers correctly identified as past) |
| **Overall** | **~90%** |

---

## Next Steps

1. Improve industry extraction to preserve full field names
2. Test with more URLs to validate pattern
3. Consider whether to extract past speakers (currently excluded per prompt rules)
