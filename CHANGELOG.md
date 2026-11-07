# Changelog

All notable changes to the **InternReach** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]
### Planned
- Automated PDF motivation letter export with LaTeX rendering.
- Email dispatch microservice for direct recruiter outreach.
- Browser extension for one-click job ingestion from LinkedIn and Indeed.

---

## [0.2.0] - 2026-11-07

### Added
- **Dynamic Live Search Tools:** Replaced static registries with purely dynamic live scraping tools:
  - `JobSpy` integration for Indeed, LinkedIn, and Glassdoor using unauthenticated mobile API extraction.
  - `ddgs` live search for Welcome to the Jungle, Apec, HelloWork, and enterprise R&D career portals (Thales, CEA, Safran, Airbus, Inria).
- **Autonomous Ingestion & Liveness Worker:**
  - FastAPI background worker running periodic sweeps (default: every 6h).
  - Asynchronous HTTP HEAD liveness checker marking closed postings (`is_active: false`).
  - Worker supervision endpoints (`GET /api/worker/status`, `POST /api/worker/trigger`, `GET/POST /api/worker/settings`).
  - UI toggle in `SearchSection` to filter out expired offers.
- **AI-Powered CV Parsing:**
  - Integrated Gemini LLM structured extraction with resilient regex fallback.
  - Multi-column scientific resume parsing (tested with Master 1/2 E3A Paris-Saclay profile).
  - Reactive `useEffect` state synchronization in `CvSection` form with visual status banner.
- **Enhanced Application Tracking CRM:**
  - Interactive status dropdown (`Prêt`, `Candidaté`, `Entretien`, `Offre`, `Refusé`) with instant `PATCH /api/history/{id}/status` persistence.
  - Delete application action with confirmation modal (`DELETE /api/history/{id}`).
  - View archived motivation letter modal.
- **Comprehensive Documentation Suite:**
  - Per-endpoint REST API reference in `docs/API.md`.
  - Architecture specifications and Mermaid sequence diagrams in `docs/ARCHITECTURE.md`.
  - Architecture Decision Records (`ADR-001`, `ADR-002`, `ADR-003`) in `docs/adr/`.
  - AI-agent guidance file in `llms.txt`.

### Fixed
- Fixed `Notice: Live search DDGS error: No results found.` caused by overly complex comma-separated search tokens and unsupported boolean operators.
- Fixed React state desynchronization in `CvSection` where uploaded CV data was received from the server but not populated into form fields.
- Fixed `history.json` duplicate IDs and missing PATCH/DELETE endpoints.
- Fixed job URL redirects displaying `http://localhost:3005/nan` when source URL was undefined.

---

## [0.1.0] - 2026-11-06

### Added
- **Initial MVP Release:**
  - FastAPI backend running on port 8008 with CORS middleware.
  - Next.js 14 App Router frontend running on port 3005.
  - Swiss Scientific design system (International Typographic Style).
  - 3-variant motivation letter generator (`scientific`, `startup`, `industrial`).
  - Iterative natural language feedback refinement loop.
  - ATS keyword gap analysis and elevator pitch generation.
  - Technical and behavioral interview question preparation.
  - BYOK (Bring Your Own Key) settings modal supporting Gemini, OpenAI, Claude, and local Ollama.
  - Double-click launcher script `start.bat`.

