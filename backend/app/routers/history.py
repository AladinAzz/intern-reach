from fastapi import APIRouter
from typing import Dict, Any, List
from app.services.storage import load_history, save_history, add_history_entry

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

