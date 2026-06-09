# QA Pipeline Test Notes

## Test URL 1: https://scholarsforum.net/event/index.php?id=100442671

### Manual Extraction (via Playwright browser snapshot)

**Conference:**
- Name: International Conference on Ocean-Borne Diseases and Biological Contaminants (ICOBDC-26)
- Organizer: Scholars Forum
- Dates: 19th - 20th June 2026
- Venue: Munich, Germany (Hybrid — in-person or virtual)
- Industry: Ocean-Borne Diseases, Marine Biology, Environmental Science
- Session Tracks: Marine Pathogens, Ecosystem Health, Environmental Monitoring, Conservation, Microbial Monitoring
- Aligned SDGs: SDG 3 (Health), SDG 4 (Education), SDG 6 (Clean Water)

**Sub-pages found:**
| Page | URL |
|------|-----|
| Registration | registration.php?id=100442671 |
| Venue | venue.php?id=100442671 |
| Call for Papers | call_for_paper.php?id=100442671 |
| Abstract Submission | Research_Article_Submission.php?id=100442671 |
| Conference Brochure | conference-brochure.php?id=100442671 |
| Important Dates | important-dates.php?id=100442671 |
| Scientific Committee | scientific-committee.php?id=100442671 |
| Tentative Program | tentative-program.php?id=100442671 |
| Conference Speakers | test_pastspeakers.php?id=100442671 |
| Session Tracks | list-session-tracks.php?id=100442671 |

**Past Speakers (not confirmed for this edition):**
1. Dr. Jagbir Singh Narwal — Assistant Professor, Maharshi Dayanand University, Rohtak
2. Mr. Akshay Sharma — Independent Researcher, USA
3. Rajesh Vayyala — Independent Researcher, PRA Group Inc, USA

**Registration:** Early-bird registration available, Attendee Registration link, Registration Options page

### Pipeline Result
- Pipeline timed out after 300s
- First run timed out too
- Need to investigate: Scrapling MCP slowness or LLM timeout?

### Issues Found
1. URL has `?id=` query parameter — PHP-based, possibly dynamic content
2. Pipeline timeout — either Scrapling fetch hangs or LLM calls are slow
3. Page has a language translation widget (RTL Arabic dropdown) — potential MCP parsing issue
