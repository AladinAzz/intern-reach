import asyncio
import os
from collections import Counter
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

import httpx

from app.services.storage import (
    DATA_DIR,
    STORE_LOCK,
    atomic_write_json,
    read_json,
    load_stored_jobs,
    upsert_stored_jobs,
    update_jobs_liveness,
)
from app.services.registries import fetch_all_registries, load_worker_settings
from app.services.job_extractor import is_safe_url

WORKER_STATE_FILE = os.path.join(DATA_DIR, "worker_state.json")

LIVENESS_BATCH = 40          # jobs verified per cycle (least recently checked first)
LIVENESS_CONCURRENCY = 8
LIVENESS_MAX_REDIRECTS = 5
# Sites that always answer 200 (JS shells) or placeholders that are not real postings: never probed.
LIVENESS_SKIP = ("example.com", "welcometothejungle", "google.com/search")


def _default_state() -> Dict[str, Any]:
    return {
        "is_running": False,
        "last_sync": None,
        "total_jobs": 0,
        "active_jobs": 0,
        "expired_jobs": 0,
        "last_error": None,
        "sources_stats": {},
    }


def load_worker_state() -> Dict[str, Any]:
    state = _default_state()
    data = read_json(WORKER_STATE_FILE, {})
    if isinstance(data, dict):
        state.update({k: v for k, v in data.items() if k in state})
    return state


def save_worker_state(state: Dict[str, Any]) -> None:
    with STORE_LOCK:
        atomic_write_json(WORKER_STATE_FILE, state)


async def check_url_liveness(url: str, client: httpx.AsyncClient) -> Optional[bool]:
    """
    True  = posting reachable, False = definitively gone (404/410), None = inconclusive
    (bot-blocking 403/429, 5xx, timeouts, TLS errors): an inconclusive probe never marks an offer as closed.
    Redirects are followed manually so every hop passes the SSRF guard.
    """
    if not url or not url.startswith(("http://", "https://")):
        return None
    current = url
    try:
        for _ in range(LIVENESS_MAX_REDIRECTS + 1):
            if not await asyncio.to_thread(is_safe_url, current):
                return None
            status: Optional[int] = None
            location: Optional[str] = None
            for method in ("HEAD", "GET"):
                async with client.stream(method, current, timeout=6.0) as resp:
                    status = resp.status_code
                    location = resp.headers.get("location")
                if status in (404, 410):
                    return False
                if status < 400:
                    break
                # HEAD refused (403/405/501...) -> retry once with GET before concluding anything.
            if status is not None and 300 <= status < 400 and location:
                current = urljoin(current, location)
                continue
            if status is not None and status < 400:
                return True
            return None
    except httpx.HTTPError:
        return None
    except Exception:
        return None
    return None


async def verify_jobs_liveness(jobs: List[Dict[str, Any]], max_concurrent: int = LIVENESS_CONCURRENCY) -> Dict[str, Optional[bool]]:
    """Probes the least-recently-checked jobs and returns {job_id: verdict}. Nothing is persisted here."""
    candidates = [j for j in jobs if not any(skip in str(j.get("url", "")) for skip in LIVENESS_SKIP)]
    candidates.sort(key=lambda j: str(j.get("last_checked") or ""))
    batch = candidates[:LIVENESS_BATCH]

    verdicts: Dict[str, Optional[bool]] = {}
    sem = asyncio.Semaphore(max_concurrent)

    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) InternReach/2026"},
        follow_redirects=False,
    ) as client:
        async def verify_one(job: Dict[str, Any]):
            async with sem:
                verdicts[job["id"]] = await check_url_liveness(job.get("url", ""), client)

        await asyncio.gather(*[verify_one(j) for j in batch], return_exceptions=True)

    # Skipped jobs are considered active (they cannot be probed reliably).
    for j in jobs:
        if any(skip in str(j.get("url", "")) for skip in LIVENESS_SKIP):
            verdicts.setdefault(j["id"], True)
    return verdicts


class IngestionWorker:
    def __init__(self):
        self._is_syncing = False
        self._background_task: Optional[asyncio.Task] = None

    def is_syncing(self) -> bool:
        return self._is_syncing

    async def run_sync_cycle(self) -> Dict[str, Any]:
        """Ingestion (CV-driven live search), de-duplication and liveness verification."""
        if self._is_syncing:
            return load_worker_state()

        self._is_syncing = True
        state = load_worker_state()
        state["is_running"] = True
        save_worker_state(state)

        try:
            # 1. Live ingestion with keywords derived from the candidate's CV.
            fresh = await fetch_all_registries()
            if fresh:
                upsert_stored_jobs(fresh)

            # 2. Liveness verification (network sweep, not holding any lock).
            settings = load_worker_settings()
            stored = load_stored_jobs()
            if settings.get("auto_liveness_check", True) and stored:
                verdicts = await verify_jobs_liveness(stored)
                stored = update_jobs_liveness(verdicts, datetime.now().strftime("%Y-%m-%d %H:%M"))

            # 3. Statistics from the final store.
            total = len(stored)
            expired = sum(1 for j in stored if j.get("is_active") is False)
            sources = Counter(str(j.get("source") or "Autre") for j in stored)

            state = {
                "is_running": False,
                "last_sync": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_jobs": total,
                "active_jobs": total - expired,
                "expired_jobs": expired,
                "last_error": None,
                "sources_stats": dict(sources),
            }
            save_worker_state(state)
            return state

        except Exception as e:
            print(f"Error during IngestionWorker sync cycle: {type(e).__name__}: {e}")
            state = load_worker_state()
            state["is_running"] = False
            state["last_error"] = f"{type(e).__name__}: {e}"
            save_worker_state(state)
            return state

        finally:
            self._is_syncing = False

    async def _scheduled_loop(self):
        """Scheduled sync according to worker_settings.json (first run is delayed so startup stays instant)."""
        try:
            await asyncio.sleep(30)
            while True:
                try:
                    hours = max(1, int(load_worker_settings().get("scan_interval_hours", 6)))
                    await self.run_sync_cycle()
                    await asyncio.sleep(hours * 3600)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    print(f"Worker scheduler error: {e}")
                    await asyncio.sleep(600)
        except asyncio.CancelledError:
            return

    def start_background_scheduler(self):
        # A previous process killed mid-sync would otherwise leave "is_running" stuck at True forever.
        state = load_worker_state()
        if state.get("is_running"):
            state["is_running"] = False
            save_worker_state(state)
        if self._background_task is None or self._background_task.done():
            self._background_task = asyncio.create_task(self._scheduled_loop())

    def stop_background_scheduler(self):
        if self._background_task and not self._background_task.done():
            self._background_task.cancel()


ingestion_worker = IngestionWorker()
