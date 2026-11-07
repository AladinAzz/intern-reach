# InternReach

> AI-powered scientific & embedded systems internship discovery engine, multi-variant motivation letter studio, and candidate application CRM.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Quick Start

Get InternReach running locally in less than 3 minutes.

### 1. One-Click Launcher (Windows)
Double-click the **`start.bat`** file located in the project root directory. It automatically spawns the FastAPI backend (port 8008) and Next.js frontend (port 3005) in separate terminal windows.

### 2. Manual Terminal Setup

#### Backend (Terminal 1)
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py
# Server running at: http://localhost:8008
# Interactive API docs: http://localhost:8008/docs
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
- **Autonomous Ingestion & Liveness Worker:** In-process background worker running scheduled sync sweeps and asynchronous HTTP HEAD checks to flag expired offers (`is_active: false`).
- **Hybrid AI CV Parser:** Drag-and-drop resume upload (PDF/TXT up to 10 MB). Extracts candidate identity, education (Master 1/2 E3A, etc.), technical skills, and engineering projects with Gemini LLM and resilient regex fallback.
- **3-Variant Motivation Letter Studio:**
  - **R&D / Scientifique:** Tailored for research institutes (CEA, Inria, CNRS, ONERA) focusing on scientific methodology and state-of-the-art literature.
  - **Tech Agile / Startup:** Tailored for robotics and deep-tech scale-ups prioritizing fast iteration, pragmatism, and clean code.
  - **Grand Groupe Industriel:** Tailored for defense and aerospace corporations (Thales, Safran, Airbus) emphasizing safety-critical standards (ISO 26262, DO-178C).
- **Interactive Refinement Loop:** Refine any draft with conversational prompts (*"insiste plus sur FreeRTOS et supprime la mention de Java"*).
- **ATS Gap Analysis & Interview Prep:** Computes keyword alignment against recruiter expectations and generates 5 technical interview questions with winning response angles.
- **Application Tracking CRM:** Local database of applications with interactive status updates (`Prêt`, `Candidaté`, `Entretien`, `Offre`, `Refusé`), archived letter previews, and delete actions.
- **Privacy & BYOK (Bring Your Own Key):** Zero external telemetry. Works with Google Gemini (free/fast), OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet, or 100% offline via local Ollama.

---

## Configuration

InternReach stores its configuration in `backend/app/data/settings.json` and optionally reads environment variables from `.env`.

| Variable | Description | Default | Required |
|---|---|---|---|
| `PORT` | Backend HTTP port | `8008` | No |
| `HOST` | Backend bind host | `0.0.0.0` | No |
| `NEXT_PUBLIC_API_URL` | Frontend API target URL | `http://localhost:8008` | No |
| `LLM_PROVIDER` | Selected LLM backend (`gemini`, `openai`, `claude`, `ollama`) | `gemini` | Yes |
| `GEMINI_API_KEY` | Google Gemini API Key | `""` (Set in Settings Modal) | Yes (if using Gemini) |
| `OPENAI_API_KEY` | OpenAI API Key | `""` (Set in Settings Modal) | Yes (if using OpenAI) |
| `CLAUDE_API_KEY` | Anthropic Claude API Key | `""` (Set in Settings Modal) | Yes (if using Claude) |
| `OLLAMA_BASE_URL` | Base URL for local Ollama instance | `http://localhost:11434` | No |
| `OLLAMA_MODEL` | Ollama model name | `mistral` | No |

---

## Documentation

- **[REST API Reference](docs/API.md):** Complete per-endpoint documentation with parameter tables, status codes, and request/response JSON payloads.
- **[System Architecture](docs/ARCHITECTURE.md):** High-level component diagrams, ingestion workflows, liveness verification, and Swiss Scientific design system.
- **Architecture Decision Records (ADRs):**
  - [ADR-001: Dynamic Live Search Tools vs. Static Registries](docs/adr/ADR-001-dynamic-live-search-vs-static-registries.md)
  - [ADR-002: Autonomous Background Worker & Liveness Probing](docs/adr/ADR-002-autonomous-liveness-verification-worker.md)
  - [ADR-003: Hybrid AI and Regex Structured CV Extraction](docs/adr/ADR-003-hybrid-ai-cv-parsing.md)
- **[AI Agent Guidance (llms.txt)](llms.txt):** Machine-readable context guide for LLM crawlers and automated coding agents.
- **[Changelog](CHANGELOG.md):** Version history and release notes following Keep a Changelog.

---

## Testing & Quality

### Running Backend Unit & Integration Tests
```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -v
# Verified: 22 passed in test suite
```

### Running Frontend Production Build
```powershell
cd frontend
npx.cmd pnpm build
# Verified: Type-check and Next.js static optimization pass with 0 errors
```

---

## Contributing

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/dynamic-portal-probe`).
3. Commit your changes following [Conventional Commits](https://www.conventionalcommits.org/) (`git commit -m 'feat: add CNRS lab direct scraper'`).
4. Push to the branch (`git push origin feature/dynamic-portal-probe`).
5. Open a Pull Request.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
