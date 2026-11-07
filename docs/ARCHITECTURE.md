# InternReach System Architecture

> Architectural specifications, ingestion pipelines, liveness verification mechanisms, and design systems for the InternReach platform.

---

## 1. High-Level System Architecture

InternReach is structured as a decoupled client-server application engineered for maximum responsiveness, zero reliance on fragile fixed datasets, and privacy-preserving local storage.

```mermaid
flowchart TD
    subgraph Client["Presentation Layer (Next.js 14 App Router - Port 3005)"]
        UI["Swiss Scientific UI Engine"]
        SearchTab["Dynamic Search & Filter View"]
        CVTab["CV Upload & Structured Profile"]
        StudioTab["3-Variant Letter Studio & Feedback Loop"]
        CRMTab["Pipeline Tracker (History CRM)"]
        WorkerModal["Worker Supervision & BYOK Settings"]
    end

    subgraph Server["Backend Services (FastAPI - Port 8008)"]
        API["FastAPI REST Gateway"]
        AgentReach["Agent Reach Search Service"]
        Worker["Autonomous Ingestion Worker"]
        CVParser["AI CV Parser (Gemini / Claude / Regex)"]
        LetterGen["Multi-Variant Letter Generator"]
        Storage["Atomic JSON Storage Engine (STORE_LOCK)"]
    end

    subgraph Ingestion["Dynamic Ingestion Primitives"]
        JobSpy["JobSpy Scraper (Indeed, LinkedIn, Glassdoor)"]
        DDGS["Live DDGS Search Engine (Welcometothejungle, Apec, HelloWork)"]
        PortalProbe["Direct R&D Portals (Thales, CEA, Safran, Inria)"]
        Liveness["Tri-State HTTP HEAD/GET Prober"]
    end

    subgraph LLM["Inference Providers (BYOK)"]
        Gemini["Google Gemini 1.5/2.0 Flash"]
        OpenAI["OpenAI GPT-4o"]
        Claude["Anthropic Claude 3.5 Sonnet"]
        Ollama["Local Ollama (Offline)"]
    end

    UI --> API
    API --> AgentReach
    API --> Worker
    API --> CVParser
    API --> LetterGen
    API --> Storage

    AgentReach --> JobSpy
    AgentReach --> DDGS
    AgentReach --> PortalProbe
    Worker --> Liveness
    Worker --> AgentReach

    CVParser --> LLM
    LetterGen --> LLM
```

---

## 2. Ingestion & Dynamic Search Flow

InternReach eliminates static registries in favor of live multi-source scraping with intelligent query partitioning and deduplication:

```mermaid
sequenceDiagram
    autonumber
    actor Candidate as Candidate
    participant UI as Next.js 14 Frontend
    participant API as FastAPI Gateway
    participant Reach as AgentReach Service
    participant JobSpy as JobSpy Engine
    participant DDGS as DDGS Web Engine
    participant Storage as Local JSON Store (Atomic)

    Candidate->>UI: Selects domain ("Systèmes Embarqués") or clicks "POPULER AVEC L'IA"
    UI->>API: POST /api/search {query, location}
    API->>Reach: search_internships_async()
    
    par Live Multi-Board Scraping
        Reach->>JobSpy: Scrape Indeed, LinkedIn, Glassdoor (mobile REST API)
        JobSpy-->>Reach: Normalized candidate offers (DataFrames)
    and Live Specialized Web Search
        Reach->>DDGS: Search localized ATS & specialized French job portals
        DDGS-->>Reach: Extracted live postings
    end

    Reach->>Storage: upsert_stored_jobs() (Deduplicate via Canonical URL & SHA-1 ID)
    Reach->>Reach: Calculate ATS matching score against Candidate Profile
    Reach-->>API: Filtered, enriched, and sorted job offers
    API-->>UI: JSON {status: "success", total: N, results: [...]}
    UI-->>Candidate: Renders high-density Swiss Scientific cards
```

---

## 3. Autonomous Ingestion Worker & Liveness Loop

The background ingestion worker runs on a configurable cadence (default: every 6 hours) to discover new postings and verify the liveness of stored listings without false positives:

```mermaid
flowchart TD
    Start["Worker Cycle Triggered (Cron / Manual POST /api/worker/trigger)"] --> ReadConfig["Load worker_settings.json"]
    ReadConfig --> IngestionStep["Ingestion Step: Query Live Tools (CV-derived terms)"]
    IngestionStep --> Deduplicate["Deduplicate & Upsert New Offers (stable_job_id)"]
    Deduplicate --> LivenessCheck{"Auto Liveness Enabled?"}
    
    LivenessCheck -- Yes --> BatchSelection["Select Oldest 40 Checked Jobs"]
    BatchSelection --> ProbeHTTP["Async Probing (HEAD + GET fallback, Concurrency: 8)"]
    ProbeHTTP --> EvalVerdict{"HTTP Status Evaluation"}
    
    EvalVerdict -- "2xx / 3xx" --> MarkActive["Verdict: True (is_active: true)"]
    EvalVerdict -- "404 / 410" --> MarkClosed["Verdict: False (is_active: false)"]
    EvalVerdict -- "403 / 429 / 5xx / Timeout" --> KeepState["Verdict: None (Preserve Current State)"]
    
    MarkActive --> UpdateStorage["update_jobs_liveness() under STORE_LOCK"]
    MarkClosed --> UpdateStorage
    KeepState --> UpdateStorage
    
    LivenessCheck -- No --> SaveState["Save worker_state.json"]
    UpdateStorage --> SaveState
    SaveState --> End["Cycle Completed (Sleep until next interval)"]
```

---

## 4. Security Architecture & Threat Defense

### 4.1 Multi-Hop SSRF Defense
External offer ingestion (`POST /api/search/import-offer`) poses a high Server-Side Request Forgery risk. The application enforces a multi-layer guard before making outbound HTTP requests:
1. **Scheme & Port Check:** Only `http` and `https` on ports `80` and `443` are accepted. Embedded credentials (`user:pass@host`) are rejected.
2. **DNS Multi-IP Verification:** Every IP returned by DNS is parsed into an `ipaddress` object. The request is aborted if any IP belongs to:
   - Loopback (`127.0.0.0/8`, `::1`)
   - RFC 1918 Private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
   - Link-local and cloud metadata (`169.254.0.0/16`, `fe80::/10`)
   - IPv4-mapped IPv6 notation (`::ffff:127.0.0.1`)
   - Internal top-level domains (`.local`, `.internal`, `.localhost`)
3. **Manual Redirect Inspection:** Automated redirect following is disabled. Up to 3 HTTP redirect hops are resolved and re-verified against the full SSRF validation routine before following.

### 4.2 API Key Transport & Masking
- **Header-Based Transport:** Google Gemini keys are sent via `x-goog-api-key` headers rather than URL query parameters, preventing key exposure in server access logs and proxy captures.
- **Egress Masking:** Server responses from `GET /api/settings` mask secret keys (`...xxxx`), storing full keys only in the local, git-ignored `settings.json` file.
- **CORS Restriction:** Local-only origins (`http://localhost:3005`, `http://127.0.0.1:3005`) with `allow_credentials=False`. Default binding restricted to `127.0.0.1`.

---

## 5. Storage Engine & Concurrency Control

All persistence in InternReach relies on local JSON documents within `backend/app/data/`:
- `profile.json`: Structured candidate profile, technical skills, target domains, and key projects.
- `jobs.json`: Deduplicated catalog of ingested job offers with metadata and liveness status.
- `history.json`: CRM pipeline records of applied and tracked positions.
- `settings.json`: BYOK API keys and model configurations.
- `worker_settings.json` & `worker_state.json`: Background worker schedules and sync telemetry.

### Concurrency & Atomic Writes
- **Process Lock:** All file updates are synchronized with a reentrant lock (`STORE_LOCK = threading.RLock()`).
- **Atomic File Swaps:** Files are written to a temporary sibling file via `tempfile.NamedTemporaryFile` and replaced atomically using `os.replace`, preventing partially written files during unexpected server terminations.
- **Test Isolation:** The `INTERN_REACH_DATA_DIR` environment variable allows automated test harnesses (`pytest`) to redirect all file I/O to a temporary scratch directory without touching production data.

---

## 6. Swiss Scientific Design System Specification

The user interface adheres to the **International Typographic Style** (Swiss Style), emphasizing clarity, structure, and functional minimalism:

| Element | Specification | Rationale |
|---|---|---|
| **Primary Typography** | `Inter`, sans-serif | High legibility for long-form scientific text and letter review. |
| **Monospace Typography** | `JetBrains Mono`, monospace | Technical metadata, ATS match scores, tags, and code badges. |
| **Primary Accent** | Cobalt Blue (`#0047AB`) | Rigorous, high-contrast, authoritative visual anchor. |
| **Neutral Background** | Clinical Light Grey (`#F8F9FA`) | Reduced eye fatigue during prolonged reading sessions. |
| **Card & Container Background** | Pure White (`#FFFFFF`) | Elevated surface contrast with minimal 1px borders (`#E2E8F0`). |
| **Emoji Policy** | Strictly Prohibited in UI Controls | Decorative emojis undermine scientific authority. Pure SVGs only. |

---

## 7. Architecture Decision Records (ADRs)

- [ADR-001: Dynamic Live Search Tools vs. Static Registries](adr/ADR-001-dynamic-live-search-vs-static-registries.md)
- [ADR-002: Autonomous Background Worker & Liveness Probing](adr/ADR-002-autonomous-liveness-verification-worker.md)
- [ADR-003: Hybrid AI and Regex Structured CV Extraction](adr/ADR-003-hybrid-ai-cv-parsing.md)
- [ADR-004: SSRF Defense, Concurrency Locking & Atomic File Storage](adr/ADR-004-ssrf-defense-and-storage-concurrency.md)
