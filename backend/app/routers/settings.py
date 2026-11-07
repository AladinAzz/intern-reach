from typing import Optional, Literal
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.services.storage import load_settings, save_settings

router = APIRouter(prefix="/api/settings", tags=["Settings"])

KEY_FIELDS = ("gemini_api_key", "openai_api_key", "claude_api_key")


class SettingsIn(BaseModel):
    active_provider: Literal["gemini", "openai", "claude", "ollama", "mock"] = "gemini"
    gemini_api_key: Optional[str] = Field(None, max_length=500)
    openai_api_key: Optional[str] = Field(None, max_length=500)
    claude_api_key: Optional[str] = Field(None, max_length=500)
    ollama_base_url: str = Field("http://localhost:11434", max_length=500)
    ollama_model: str = Field("llama3:latest", max_length=200)


def mask_key(key: str) -> str:
    """Never return a stored secret in clear: short keys are fully masked."""
    if not key:
        return ""
    if len(key) < 12:
        return "..." + key[-2:]
    return f"{key[:4]}...{key[-4:]}"


def _masked(settings: dict) -> dict:
    out = dict(settings)
    for key_field in KEY_FIELDS:
        if out.get(key_field):
            out[key_field] = mask_key(out[key_field])
    return out


@router.get("")
def get_settings():
    return _masked(load_settings())


@router.post("")
def update_settings(data: SettingsIn):
    current = load_settings()
    new = data.model_dump()
    # Empty / null / masked values keep the stored secret (the UI only ever sees the masked form).
    for key_field in KEY_FIELDS:
        new_val = (new.get(key_field) or "").strip()
        if not new_val or "..." in new_val:
            new[key_field] = current.get(key_field, "")
        else:
            new[key_field] = new_val
    save_settings(new)
    return {"status": "saved", "settings": _masked(new)}
