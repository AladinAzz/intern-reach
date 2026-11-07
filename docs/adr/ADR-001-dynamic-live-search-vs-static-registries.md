# ADR-001: Dynamic Live Search Tools vs. Static Registries

## Status
Accepted

## Context
Early prototypes of internship discovery scrapers relied on static registries (e.g., cloned GitHub repositories like `SimplifyJobs/Summer2027-Internships` or periodic static JSON dumps). In practice, early-career recruitment across France and Europe suffers from high obsolescence:
1. High-demand scientific and embedded systems internships at organizations such as Thales, CEA, Inria, and Safran frequently close within 72 hours of publication.
2. Static registries focus predominantly on North American SWE (Software Engineering) roles, ignoring European R&D labs, deep-tech hardware startups, and regional defense contractors.
3. Hardcoding static fallback datasets results in stale URLs, broken redirects (e.g. `http://localhost:3005/nan`), and applicant frustration.

## Decision
We decided to completely deprecate static registries and replace them with purely dynamic live search tooling:
1. **Multi-Board Scraping via `JobSpy`:** Query unauthenticated mobile REST API endpoints for Indeed, LinkedIn, and Glassdoor with real-time location filtering (`Paris, Île-de-France`).
2. **Live Specialized Web Search via `ddgs`:** Dynamic web queries targeting specialized French career boards (Welcome to the Jungle, Apec, HelloWork) and enterprise career portals (Thales, CEA, Safran, Airbus, STMicroelectronics).
3. **Local Upsert Deduplication:** Dynamically scraped offers are upserted into an indexed local JSON store (`stored_jobs.json`) using canonical URL and title/company hashing, ensuring deduplication and fast repeated queries.

## Consequences
### Positive:
- Always fresh listings reflecting current active recruitment cycles.
- Direct coverage of French R&D, embedded systems, robotics, and aerospace sectors.
- Resilient against anti-bot Cloudflare challenges through unauthenticated mobile endpoints.

### Negative / Trade-offs:
- Search latency increases from ~50ms (reading static JSON) to ~2-4s (live network queries).
- Requires defensive exception handling (e.g. handling DDGS rate limits or empty results gracefully).
