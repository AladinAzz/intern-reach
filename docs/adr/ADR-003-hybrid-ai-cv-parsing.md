# ADR-003: Hybrid AI and Regex Structured CV Extraction

## Status
Accepted

## Context
Scientific and engineering resumes in France (particularly from universities like Paris-Saclay, Sorbonne, or engineering Grandes Écoles) feature diverse formatting: multi-column PDF layouts, academic laboratory projects (e.g. LATMOS, CNRS), technical skill taxonomies (FreeRTOS, FPGA Vivado, ROS 2, STM32), and French telephone/address formats.
Traditional regex-only extractors fail to capture complex project narratives, while relying solely on external LLMs risks failure if the user is offline or has not configured an API key.

## Decision
We implemented a two-tier hybrid parsing architecture:
1. **Tier 1 (AI-Powered Extraction):** When a configured LLM provider (Google Gemini, OpenAI, Claude, or local Ollama) is accessible, the extracted PDF text is submitted to a structured schema prompt requesting JSON output (`name`, `email`, `phone`, `education`, `skills`, `projects`, `experience`).
2. **Tier 2 (Defensive Regex Fallback):** If no LLM key is configured or the LLM request fails, the parser falls back to resilient regex patterns (matching French phone formats `+33 ...` / `06 ...`, RFC-compliant email matching, and keyword dictionary extraction for scientific skills).
3. **Frontend Reactive Synchronization:** The Next.js frontend synchronizes incoming extracted profile data via `useEffect` into editable form inputs, allowing instant candidate review and manual adjustments.

## Consequences
### Positive:
- High semantic accuracy: accurately isolates candidate names, degrees (Master 1/2 E3A), and multi-sentence engineering project summaries.
- Fault-tolerant: degrades gracefully to local heuristic extraction when offline.
- Immediate visual confirmation in the UI with zero data loss.

### Negative / Trade-offs:
- LLM parsing adds ~1-2 seconds of latency during initial CV upload.
