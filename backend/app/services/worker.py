import asyncio
import json
import os
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.services.storage import load_stored_jobs, save_stored_jobs, upsert_stored_jobs
from app.services.registries import fetch_all_registries, load_worker_settings

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
WORKER_STATE_FILE = os.path.join(DATA_DIR, "worker_state.json")

def load_worker_state() -> Dict[str, Any]:
    if os.path.exists(WORKER_STATE_FILE):
        try:
            with open(WORKER_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "is_running": False,
        "last_sync": None,
        "total_jobs": 0,
        "active_jobs": 0,
        "expired_jobs": 0,
        "last_error": None,
        "sources_stats": {
            "SimplifyJobs": 0,
            "European Tech": 0,
            "speedyapply": 0,
            "JobSpy / Curated": 0
        }
    }

def save_worker_state(state: Dict[str, Any]) -> None:
    with open(WORKER_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

async def check_url_liveness(url: str, client: httpx.AsyncClient) -> bool:
    """
    Asynchronously checks whether a job application URL remains active.
    Uses HTTP HEAD with fallback to GET (streaming 10 bytes).
    """
    if not url or url == "nan" or not url.startswith("http"):
        return False
    try:
        # Fast HEAD request
        res = await client.head(url, timeout=3.5, follow_redirects=True)
        if res.status_code in (200, 201, 204, 301, 302, 307, 308):
            return True
        if res.status_code in (404, 410):
            return False
    except Exception:
        pass

    try:
        # Fallback shallow GET request (some servers block HEAD)
        res = await client.get(url, timeout=3.5, follow_redirects=True)
        return res.status_code < 400
    except Exception:
        # If timeout or temporary network hiccup, assume still active
        return True

async def verify_jobs_liveness(jobs: List[Dict[str, Any]], max_concurrent: int = 10) -> List[Dict[str, Any]]:
    """
    Verifies URL liveness concurrently across jobs using an asyncio Semaphore.
    """
    sem = asyncio.Semaphore(max_concurrent)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) InternReach/2026"},
        verify=False
    ) as client:
        async def verify_one(job: Dict[str, Any]):
            url = job.get("url", "")
            # Skip checking internal or mock URLs
            if not url or "example.com" in url or "welcometothejungle" in url:
                job["is_active"] = True
                job["last_checked"] = now_str
                return

            async with sem:
                is_active = await check_url_liveness(url, client)
                job["is_active"] = is_active
                job["last_checked"] = now_str

        # Check up to 30 most recent jobs to conserve bandwidth
        sample = jobs[:30]
        await asyncio.gather(*[verify_one(j) for j in sample], return_exceptions=True)

    return jobs

class IngestionWorker:
    def __init__(self):
        self._is_syncing = False
        self._background_task: Optional[asyncio.Task] = None

    def is_syncing(self) -> bool:
        return self._is_syncing

    async def run_sync_cycle(self) -> Dict[str, Any]:
        """
        Executes a complete ingestion, deduplication, and liveness verification cycle.
        """
        if self._is_syncing:
            return load_worker_state()

        self._is_syncing = True
        state = load_worker_state()
        state["is_running"] = True
        save_worker_state(state)

        try:
            # 1. Ingest from open-source GitHub registries
            registry_offers = await fetch_all_registries()

            # 2. Ingest existing stored jobs
            current_stored = load_stored_jobs()

            # 3. Deduplicate and merge
            combined = upsert_stored_jobs(registry_offers + current_stored)

            # 4. Run Liveness Verification
            settings = load_worker_settings()
            if settings.get("auto_liveness_check", True):
                verified = await verify_jobs_liveness(combined)
            else:
                verified = combined

            # 5. Persist to jobs.json
            save_stored_jobs(verified)

            # 6. Compute statistics
            total = len(verified)
            active_count = sum(1 for j in verified if j.get("is_active", True) is not False)
            expired_count = total - active_count

            sources_stats = {
                "JobSpy Live": sum(1 for j in verified if "JobSpy" in str(j.get("source", ""))),
                "Live Web (WTTJ, Apec, LinkedIn)": sum(1 for j in verified if any(k in str(j.get("source", "")) for k in ("WTTJ", "Apec", "LinkedIn", "Web", "Jungle"))),
                "Portails R&D & Entreprises": sum(1 for j in verified if any(k in str(j.get("source", "")) for k in ("Labo R&D", "Thales", "CEA", "Safran", "Airbus"))),
            }

            state = {
                "is_running": False,
                "last_sync": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_jobs": total,
                "active_jobs": active_count,
                "expired_jobs": expired_count,
                "last_error": None,
                "sources_stats": sources_stats
            }
            save_worker_state(state)
            return state

        except Exception as e:
            print(f"Error during IngestionWorker sync cycle: {e}")
            state = load_worker_state()
            state["is_running"] = False
            state["last_error"] = str(e)
            save_worker_state(state)
            return state

        finally:
            self._is_syncing = False

    async def _scheduled_loop(self):
        """Infinite loop executing scheduled sync according to worker_settings.json."""
        while True:
            try:
                settings = load_worker_settings()
                hours = max(1, settings.get("scan_interval_hours", 6))
                await self.run_sync_cycle()
                await asyncio.sleep(hours * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker scheduler error: {e}")
                await asyncio.sleep(600)

    def start_background_scheduler(self):
        if self._background_task is None or self._background_task.done():
            self._background_task = asyncio.create_task(self._scheduled_loop())

    def stop_background_scheduler(self):
        if self._background_task and not self._background_task.done():
            self._background_task.cancel()

ingestion_worker = IngestionWorker()

