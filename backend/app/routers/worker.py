from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict, Any
from app.services.worker import ingestion_worker, load_worker_state
from app.services.registries import load_worker_settings, save_worker_settings

router = APIRouter(prefix="/api/worker", tags=["Worker"])

@router.get("/status")
def get_status():
    return load_worker_state()

@router.post("/trigger")
async def trigger_sync(background_tasks: BackgroundTasks):
    if ingestion_worker.is_syncing():
        return {
            "status": "already_running",
            "message": "Un cycle de synchronisation et de vérification est déjà en cours d'exécution.",
            "state": load_worker_state()
        }
    
    # Run in background or directly
    state = await ingestion_worker.run_sync_cycle()
    return {
        "status": "completed",
        "message": "Synchronisation multi-sources et vérification de liveness terminées.",
        "state": state
    }

@router.get("/settings")
def get_settings():
    return load_worker_settings()

@router.post("/settings")
def update_settings(payload: Dict[str, Any]):
    save_worker_settings(payload)
    return {
        "status": "updated",
        "settings": payload
    }

