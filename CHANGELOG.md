# Changelog

All notable changes to the **InternReach** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Automated LaTeX-to-PDF compiled motivation letter download.
- SMTP / Gmail direct recruiter dispatch integration.
- Desktop notifications for newly detected scientific internship openings.

---

## [0.3.0] - 2026-11-07

### Added
- **Automated Windows Setup (`setup.bat`):**
  - Added one-click installation script checking Python 3.10+ and Node.js LTS in PATH.
  - Automatically provisions `backend/venv`, installs `requirements.txt` and `requirements-dev.txt`, initializes `.env`, and installs frontend dependencies with `pnpm` (or `npm`).
  - Added interactive prompt to immediately launch via `start.bat`.
- **Improved Platform Launcher (`start.bat`):**
  - Hardened Windows batch syntax with CRLF line endings, ping-based delay compatible with redirection, and clean dual-window spawning for FastAPI (port 8008) and Next.js (port 3005).
- **Technical Interview Simulator Modal:**
  - Integrated full interview simulator modal into `LetterStudio.tsx` displaying 5 tailored technical questions, expected response angles, and recruiter advice.
  - Added "Régénérer" button to re-query `/api/letters/interview-prep` and automatic question reset when switching jobs.
- **Dynamic CV Keywords & Domains Management:**
  - Added Target Domains (`target_domains`) tag manager and Key Projects CRUD in `CvSection.tsx`.
  - Added "POPULER AVEC L'IA" button leveraging `/api/search/suggest-keywords` to synthesize optimal multi-angle queries directly from the candidate's CV profile.
  - Completely decoupled job search from hardcoded presets: all keywords originate dynamically from the uploaded CV.
- **Comprehensive Test Suites:**
  - Added `backend/tests/conftest.py` with `INTERN_REACH_DATA_DIR` temp directory isolation so `pytest` never alters live user data (`profile.json`, `history.json`, `jobs.json`).
  - Expanded unit and integration test coverage from 22 to 84 tests across `test_api.py`, `test_services.py`, and `test_worker.py`.
  - Built live E2E API verification suite (`scratch/e2e_api.py`) testing live multi-board ingestion, SSRF attack vectors, and CRUD contracts.
  - Built headless Chromium browser E2E test suite (`scratch/e2e_browser.py`) via Playwright covering complete candidate workflows with 0 console or page errors.

### Security
- **Strict Multi-Hop SSRF Defense:**
  - Hardened `is_safe_url` in `job_extractor.py` to validate every DNS-resolved IP address.
  - Enforced strict blocking of private IP ranges (RFC 1918), loopback (`127.0.0.0/8`), link-local (`169.254.0.0/16`), IPv4-mapped IPv6 (`::ffff:127.0.0.1`), reserved ranges, internal hostnames (`.local`, `.internal`), and non-HTTP ports.
  - Implemented manual redirect inspection up to 3 hops—re-validating the SSRF guard before following every 3xx redirect.
  - Replaced fake `"unsafe-url-blocked"` job record pollution with clean `ExtractionError` (HTTP 400/422/502) returns.
- **API Key Leakage Prevention:**
  - Migrated Google Gemini API key transmission from URL query parameters (`?key=...`) to standard `x-goog-api-key` HTTP request headers to prevent exposure in logs and proxy traces.
  - Restricted CORS to local origins `http://localhost:3005` and `http://127.0.0.1:3005` with `allow_credentials=False`.
  - Bound default Uvicorn server host to `127.0.0.1`.

### Changed
- **Atomic File Storage & Concurrency Control:**
  - Implemented `STORE_LOCK` (`threading.RLock()`) and `atomic_write_json` (`tempfile` + `os.replace`) in `storage.py` to eliminate data corruption during concurrent background syncs and user actions.
  - Replaced index-based job identifiers (`live-jobspy-comp-0`) with deterministic SHA-1 hashes (`stable_job_id`) formatted as `job-<sha1[:14]>`.
  - Updated `canonical_url` to preserve essential job identity query parameters (e.g. `jk` and `vjk` on Indeed) while stripping tracking parameters (`utm_*`, `trk`).
- **Tri-State Liveness Probing:**
  - Refactored `check_url_liveness` in `worker.py` to return tri-state verdicts: `True` (reachable), `False` (definitively 404/410), or `None` (inconclusive on 403/429 anti-bot responses or timeouts). Inconclusive checks preserve existing offer state, eliminating false-positive closures.
  - Applied liveness updates under `STORE_LOCK` via `update_jobs_liveness` without clobbering newly ingested offers.
- **Client Error Handling & Validation:**
  - Enhanced `frontend/src/lib/api.ts` to surface detailed backend error messages instead of generic fallbacks.
  - Added user-facing error banners in `CvSection`, `SearchSection` (import modal and AI suggestion), and `LetterStudio`.
  - Normalized `target_sites` in `SettingsModal.tsx` and `types/index.ts` to support both string and array representations without runtime type errors.

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
  - Interactive status dropdown (`Enregistré`, `Candidaté`, `Entretien`, `Accepté`, `Refusé`) with instant `PATCH /api/history/{id}/status` persistence.
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
