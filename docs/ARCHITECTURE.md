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
        CVParser["AI CV Parser (Gemini / Regex)"]
        LetterGen["Multi-Variant Letter Generator"]
        Storage["Atomic JSON Storage Engine"]
    end

    subgraph Ingestion["Dynamic Ingestion Primitives"]
        JobSpy["JobSpy Scraper (Indeed, LinkedIn, Glassdoor)"]
        DDGS["Live DDGS Search Engine (Welcometothejungle, Apec, HelloWork)"]
        PortalProbe["Direct R&D Portals (Thales, CEA, Safran, Inria)"]
        Liveness["Async HTTP HEAD Prober"]
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
    actor Diner as Candidate
    participant UI as Next.js 14 Frontend
    participant API as FastAPI Gateway
    participant Reach as AgentReach Service
    participant JobSpy as JobSpy Engine
    participant DDGS as DDGS Web Engine
    participant Storage as Local JSON Store

    Diner->>UI: Selects domain ("Systèmes Embarqués") & clicks Search
    UI->>API: POST /api/search {query, location}
    API->>Reach: search_internships_async()
    
    par Live Multi-Board Scraping
        Reach->>JobSpy: Scrape Indeed, LinkedIn, Glassdoor (mobile REST API)
        JobSpy-->>Reach: Normalized candidate offers (DataFrames)
    and Live Specialized Web Search
        Reach->>DDGS: Search localized ATS & specialized French job portals
        DDGS-->>Reach: Extracted live postings
    end

    Reach->>Storage: upsert_stored_jobs() (Deduplicate via MD5 / Canonical URL)
    Reach->>Reach: Calculate ATS matching score against Candidate Profile
    Reach-->>API: Filtered, enriched, and sorted job offers
    API-->>UI: JSON {status: "success", total: N, results: [...]}
    UI-->>Diner: Renders high-density Swiss Scientific cards
```

---

## 3. Autonomous Ingestion Worker & Liveness Loop

To prevent candidates from applying to expired job offers (HTTP 404 or closed career boards), the background worker performs asynchronous HEAD/GET probes and marks inactive postings.

```mermaid
flowchart LR
    A["Scheduled Trigger (Every 6h)"] --> B["Trigger Multi-Source Scrape"]
    B --> C["Deduplicate & Index New Jobs"]
    C --> D["Extract All Tracked URLs"]
    D --> E["Async HTTP HEAD Sweep (Concurrency = 5)"]
    E --> F{"Response Code"}
    F -->|200 / 301 / 302| G["Mark Active: is_active = True"]
    F -->|404 / 410 / Closed| H["Mark Inactive: is_active = False"]
    G --> I["Persist to storage.py"]
    H --> I
    I --> J["Update Worker Metrics State"]
```

---

## 4. Multi-Variant Motivation Letter Generation Pipeline

The letter generation engine analyzes the semantic gap between the candidate's CV and the recruiter's specifications, producing three distinct variants:

```mermaid
flowchart TD
    Job["Target Job Offer (Title, Company, Description)"] --> Context["Context Merger"]
    CV["Candidate Profile (Skills, Projects, Education)"] --> Context
    
    Context --> Gap["ATS Gap Analysis & Pitch Synthesizer"]
    
    Gap --> V1["Variant 1: R&D / Scientifique\n(Methodology, State-of-the-Art, Lab Rigor)"]
    Gap --> V2["Variant 2: Tech Agile / Startup\n(Pragmatism, Fast Iteration, Clean Code)"]
    Gap --> V3["Variant 3: Grand Groupe Industriel\n(Safety-Critical Standards, DO-178C, ISO 26262)"]
    
    V1 --> Output["Interactive Letter Studio"]
    V2 --> Output
    V3 --> Output
    
    Output --> Feedback["Human-in-the-Loop Feedback: 'Insiste plus sur FreeRTOS'"]
    Feedback --> Refine["POST /api/letters/refine"]
    Refine --> Output
```

---

## 5. Security & BYOK Architecture

1. **Zero Cloud Credential Leakage:** API keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `CLAUDE_API_KEY`) are stored locally in `backend/app/data/settings.json` and never transmitted to external telemetry or third parties.
2. **Masked Egress:** Endpoints returning settings (`GET /api/settings`) mask keys (`AIzaSy...4aB1`). Updating settings without re-entering the key preserves stored secrets safely.
3. **Local File Size Quotas:** CV uploads are capped strictly at 10 MB in memory with explicit `413 Payload Too Large` rejection to prevent resource exhaustion attacks.

---

## 6. Swiss Scientific Design System Specifications

The visual interface is built according to the **International Typographic Style (Swiss Style / Müller-Brockmann Grid)**:
- **Primary Color:** `#0047AB` (Cobalt Scientific Blue)
- **Background Color:** `#F8F9FA` (Clean Clinical Paper White)
- **Text Color:** `#121212` (Ultra-high contrast dark charcoal)
- **Borders & Dividers:** `1px solid #E5E7EB`
- **Typography:**
  - Headers & Technical Data: `JetBrains Mono`, `monospace`
  - Body & Long-form text: `Inter`, `sans-serif`
- **Visual Hygiene:** Strict avoidance of emojis in UI headers, buttons, and system badges; use of minimalist SVG wireframe icons and monochrome status pills.

