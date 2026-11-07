# InternReach

> AI-powered scientific & embedded systems internship discovery engine, multi-variant motivation letter studio, and candidate application CRM.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-84%20Passing-brightgreen.svg)](#testing--quality)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Quick Start

Get InternReach running locally in less than 3 minutes.

### 1. Automated Setup & Launcher (Windows)

1. **One-Time Installation:** Double-click **`setup.bat`** in the project root. It automatically:
   - Verifies Python 3.10+ and Node.js LTS installations.
   - Creates the Python virtual environment (`backend/venv`) and installs all backend dependencies.
   - Initializes `backend/.env` from `.env.example`.
   - Installs frontend packages via `pnpm` (or `npm`).
   - Offers to immediately launch the application.

2. **Daily Launch:** Double-click **`start.bat`** to start both the FastAPI backend (port `8008`) and Next.js frontend (port `3005`) in separate background windows and open your browser automatically.

### 2. Manual Terminal Setup

#### Backend (Terminal 1)
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py
# Server running at: http://127.0.0.1:8008
# Interactive API docs: http://127.0.0.1:8008/docs
```

#### Frontend (Terminal 2)
```powershell
cd frontend
npx.cmd pnpm install
npx.cmd pnpm dev
# Web application running at: http://localhost:3005
```

Open [http://localhost:3005](http://localhost:3005) in your web browser.

---

## Features

- **Dynamic Multi-Source Ingestion:** Real-time job discovery powered by `JobSpy` (unauthenticated mobile REST scraping across Indeed, LinkedIn, and Glassdoor) and `ddgs` (French tech boards such as Welcome to the Jungle, Apec, HelloWork, and R&D portals like Thales, CEA, Safran, Inria). Zero reliance on stale static datasets.
- **Autonomous Ingestion & Liveness Worker:** In-process background worker running scheduled sync sweeps and tri-state HTTP liveness checks (`True` / `False` / `None`), preventing false-positive closures from 403/429 anti-bot responses.
- **Hybrid AI CV Parser & Dynamic Specialities:** Drag-and-drop resume upload (PDF/TXT up to 10 MB). Extracts candidate identity, education, target domains, technical skills, and engineering projects with Gemini LLM and resilient regex fallback. No hardcoded search queries—all search keywords dynamically derive from the candidate's CV profile.
- **AI Query Optimizer:** "POPULER AVEC L'IA" button generates targeted multi-angle search queries from candidate CV skills and domains via `/api/search/suggest-keywords`.
- **3-Variant Motivation Letter Studio:**
  - **R&D / Scientifique:** Tailored for research institutes (CEA, Inria, CNRS, ONERA) focusing on scientific methodology and state-of-the-art literature.
  - **Tech Agile / Startup:** Tailored for robotics and deep-tech scale-ups prioritizing fast iteration, pragmatism, and clean code.
  - **Grand Groupe Industriel:** Tailored for defense and aerospace corporations (Thales, Safran, Airbus) emphasizing safety-critical standards (ISO 26262, DO-178C).
- **Interactive Refinement Loop:** Refine any draft with conversational prompts (*"insiste plus sur mon projet Zynq UltraScale+ en INT8 et raccourcis à 3 paragraphes"*).
- **Direct Outreach Pitch Cards:** Auto-generates a high-impact Cold Email pitch and a recruiter LinkedIn connection note (<300 characters) directly in the Letter Studio.
- **Technical Interview Simulator:** Interactive modal anticipating 5 technical questions tailored to the targeted offer and profile, complete with expected response angles and recruiter advice.
- **Application Tracking CRM:** Local database of applications with interactive status updates (`Enregistré`, `Candidaté`, `Entretien`, `Accepté`, `Refusé`), archived letter preview drawer, PDF print export, and delete actions.
- **Hardened Security & Privacy (BYOK):** Multi-hop SSRF defense with DNS IP resolution checks, loopback/private IP blocking, and header-based API key transport (`x-goog-api-key`). Works with Google Gemini, OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet, or 100% offline via local Ollama.

---

## Configuration

InternReach stores its configuration in `backend/app/data/settings.json` and optionally reads environment variables from `backend/.env`.

| Variable | Description | Default | Required |
|---|---|---|---|
| `PORT` | Backend HTTP port | `8008` | No |
| `HOST` | Backend bind host | `127.0.0.1` | No |
| `INTERN_REACH_DATA_DIR` | Custom path for storage data (used for test isolation) | `backend/app/data` | No |
| `NEXT_PUBLIC_API_URL` | Frontend API target URL | `http://localhost:8008` | No |
| `LLM_PROVIDER` | Selected LLM backend (`gemini`, `openai`, `claude`, `ollama`) | `gemini` | Yes |
| `GEMINI_API_KEY` | Google Gemini API Key | `""` (Set in BYOK Settings) | Yes (if using Gemini) |
| `OPENAI_API_KEY` | OpenAI API Key | `""` (Set in BYOK Settings) | Yes (if using OpenAI) |
| `CLAUDE_API_KEY` | Anthropic Claude API Key | `""` (Set in BYOK Settings) | Yes (if using Claude) |
| `OLLAMA_BASE_URL` | Base URL for local Ollama instance | `http://localhost:11434` | No |
| `OLLAMA_MODEL` | Ollama model name | `llama3:latest` | No |

---

## Documentation

- **[REST API Reference](docs/API.md):** Complete per-endpoint documentation with parameter tables, status codes, and request/response JSON payloads.
- **[System Architecture](docs/ARCHITECTURE.md):** High-level component diagrams, ingestion workflows, security architecture, and Swiss Scientific design system.
- **Architecture Decision Records (ADRs):**
  - [ADR-001: Dynamic Live Search Tools vs. Static Registries](docs/adr/ADR-001-dynamic-live-search-vs-static-registries.md)
  - [ADR-002: Autonomous Background Worker & Liveness Probing](docs/adr/ADR-002-autonomous-liveness-verification-worker.md)
  - [ADR-003: Hybrid AI and Regex Structured CV Extraction](docs/adr/ADR-003-hybrid-ai-cv-parsing.md)
  - [ADR-004: SSRF Defense, Concurrency Locking & Atomic File Storage](docs/adr/ADR-004-ssrf-defense-and-storage-concurrency.md)
- **[AI Agent Guidance (llms.txt)](llms.txt):** Machine-readable context guide for LLM crawlers and automated coding agents.
- **[Changelog](CHANGELOG.md):** Version history and release notes following Keep a Changelog.

---

## Testing & Quality

### 1. Backend Unit & Integration Tests (pytest)
Isolated execution using `conftest.py` with temporary storage—never overwrites live candidate profiles or CRM history:
```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -v
# Result: 84 passed, 0 failures in ~5.6s
```

### 2. Live API End-to-End Suite
Runs full API lifecycle checks against the active server (file upload, SSRF injection attacks, multi-board search, letter generation, history CRUD, settings validation):
```powershell
python scratch/e2e_api.py
# Result: 44 checks passed (FAILED: none)
```

### 3. Headless Chromium Browser E2E Suite (Playwright)
Executes full user journeys in real Chromium browser (drag-and-drop CV, AI query population, SSRF error handling in import modal, interview simulator modal, status updates):
```powershell
python scratch/e2e_browser.py
# Result: 26/26 checks passed, 0 page errors, 0 console errors
```

### 4. Frontend Production Build
```powershell
cd frontend
npx.cmd pnpm build
# Result: Compiled successfully with zero type or lint errors
```

---

## Design System

InternReach implements the **Swiss Scientific Style** (International Typographic Style):
- **Typography:** `Inter` for prose and headings, `JetBrains Mono` for metadata, scores, and technical tags.
- **Color Palette:** Cobalt Blue (`#0047AB`), Clinical White (`#FFFFFF`), Light Neutral (`#F8F9FA`), Slate Border (`#E2E8F0`), and Deep Charcoal (`#121212`).
- **No Emojis:** Zero decorative emojis in UI buttons, badges, or headers. Pure clinical scientific clarity.

---

## License

[MIT](LICENSE)
