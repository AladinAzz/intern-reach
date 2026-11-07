from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.services.storage import (
    load_history,
    save_history,
    add_history_entry,
    update_history_status,
    delete_history_entry,
    clear_history,
)

router = APIRouter(prefix="/api/history", tags=["History"])

@router.get("")
def get_history():
    return load_history()

@router.post("")
def create_history_entry(entry: Dict[str, Any]):
    updated = add_history_entry(entry)
    return {"status": "saved", "history": updated}

@router.put("")
def update_history(history: List[Dict[str, Any]]):
    save_history(history)
    return {"status": "updated", "history": history}

@router.patch("/{entry_id}/status")
def patch_status(entry_id: str, payload: Dict[str, str]):
    new_status = payload.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Statut manquant")
    updated = update_history_status(entry_id, new_status)
    return {"status": "updated", "history": updated}

@router.delete("/{entry_id}")
def delete_entry(entry_id: str):
    updated = delete_history_entry(entry_id)
    return {"status": "deleted", "history": updated}

@router.delete("")
def clear_all_entries():
    updated = clear_history()
    return {"status": "cleared", "history": updated}
