from typing import Dict, Any, List, Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.storage import (
    load_history,
    save_history,
    add_history_entry,
    update_history_status,
    delete_history_entry,
    clear_history,
    HISTORY_STATUSES,
)

router = APIRouter(prefix="/api/history", tags=["History"])

StatusLiteral = Literal["Enregistré", "Candidaté", "Entretien", "Accepté", "Refusé"]


class HistoryEntryIn(BaseModel):
    id: Optional[str] = Field(None, max_length=200)
    job_title: str = Field("", max_length=500)
    company: str = Field("", max_length=300)
    location: str = Field("", max_length=300)
    url: str = Field("", max_length=2000)
    applied_at: str = Field("", max_length=100)
    status: StatusLiteral = "Enregistré"
    selected_version: str = Field("", max_length=200)
    letter_content: str = Field("", max_length=100_000)


class StatusIn(BaseModel):
    status: StatusLiteral


@router.get("")
def get_history():
    return load_history()


@router.post("")
def create_history_entry(entry: HistoryEntryIn):
    updated = add_history_entry(entry.model_dump(exclude_none=True))
    return {"status": "saved", "history": updated}


@router.put("")
def update_history(history: List[HistoryEntryIn]):
    entries = []
    seen = set()
    for h in history:
        d = h.model_dump(exclude_none=True)
        if not d.get("id") or d["id"] in seen:
            raise HTTPException(status_code=422, detail="Chaque entrée doit avoir un identifiant unique.")
        seen.add(d["id"])
        entries.append(d)
    save_history(entries)
    return {"status": "updated", "history": entries}


@router.patch("/{entry_id}/status")
def patch_status(entry_id: str, payload: StatusIn):
    updated = update_history_status(entry_id, payload.status)
    if updated is None:
        raise HTTPException(status_code=404, detail="Candidature introuvable.")
    return {"status": "updated", "history": updated}


@router.delete("/{entry_id}")
def delete_entry(entry_id: str):
    updated = delete_history_entry(entry_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Candidature introuvable.")
    return {"status": "deleted", "history": updated}


@router.delete("")
def clear_all_entries():
    updated = clear_history()
    return {"status": "cleared", "history": updated}
