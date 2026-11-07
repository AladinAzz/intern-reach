# ADR-002: Autonomous Background Worker for Ingestion and Liveness Probing

## Status
Accepted

## Context
Aggregated job postings decay rapidly over time as recruiters pull down postings or fill open quotas. Candidates clicking on expired links waste significant time attempting to apply to 404 pages or dead forms. Running external cron jobs or relying on heavy distributed task queues (e.g. Celery + Redis) introduces excessive operational complexity for local single-user or self-hosted deployment.

## Decision
We implemented a lightweight, non-blocking autonomous worker directly integrated into FastAPI's `lifespan` lifecycle:
1. **In-Process Background Thread:** A background worker running on a daemon thread with an asynchronous event loop that executes periodic sweeps (default: every 6 hours).
2. **HTTP HEAD Liveness Probing:** Uses `httpx.AsyncClient` with a concurrency limit (5 concurrent workers) and a short timeout (5 seconds) to probe tracked job URLs using `HEAD` requests (falling back to `GET` if `405 Method Not Allowed`).
3. **Soft Deactivation (`is_active: false`):** Expired jobs are not deleted (preserving candidate application history); instead, `is_active` is set to `false`, allowing the UI to dim or filter out expired postings.
4. **On-Demand Manual Trigger:** An API endpoint `POST /api/worker/trigger` allows candidates to initiate an immediate sync cycle from the settings modal.

## Consequences
### Positive:
- Zero external infrastructure requirements (no Redis, RabbitMQ, or Celery instances needed).
- Real-time visibility into active vs. inactive postings.
- Minimal bandwidth usage via HTTP `HEAD` probing instead of full body downloads.

### Negative / Trade-offs:
- Some career portals block or return HTTP 403 on automated `HEAD` probes; the prober must use realistic browser user-agent headers to avoid false positives.

