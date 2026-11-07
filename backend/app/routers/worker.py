from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.services.worker import ingestion_worker, load_worker_state
from app.services.registries import load_worker_settings, save_worker_settings

router = APIRouter(prefix="/api/worker", tags=["Worker"])


class SourceToggle(BaseModel):
    id: str = Field(..., max_length=100)
    enabled: bool


class WorkerSettingsIn(BaseModel):
    scan_interval_hours: int = Field(6, ge=1, le=168)
    auto_liveness_check: bool = True
    hide_expired_by_default: bool = False
    sources: List[SourceToggle] = Field(default_factory=list, max_length=20)
    target_locations: Optional[List[str]] = Field(None, max_length=30)

    model_config = {"extra": "ignore"}


@router.get("/status")
def get_status():
    state = load_worker_state()
    state["is_running"] = ingestion_worker.is_syncing()
    return state


@router.post("/trigger")
async def trigger_sync():
    if ingestion_worker.is_syncing():
        return {
            "status": "already_running",
            "message": "Un cycle de synchronisation et de vérification est déjà en cours d'exécution.",
            "state": load_worker_state(),
        }

    state = await ingestion_worker.run_sync_cycle()
    return {
        "status": "completed",
        "message": "Synchronisation multi-sources et vérification de liveness terminées.",
        "state": state,
    }


@router.get("/settings")
def get_settings():
    return load_worker_settings()


@router.post("/settings")
def update_settings(payload: WorkerSettingsIn):
    saved = save_worker_settings(payload.model_dump(exclude_none=True))
    return {"status": "updated", "settings": saved}
