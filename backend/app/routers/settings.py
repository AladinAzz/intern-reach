from fastapi import APIRouter
from typing import Dict, Any
from app.services.storage import load_settings, save_settings

router = APIRouter(prefix="/api/settings", tags=["Settings"])

def mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return key
    return f"{key[:6]}...{key[-4:]}"

@router.get("")
def get_settings():
    settings = load_settings()
    masked = dict(settings)
    for key_field in ("gemini_api_key", "openai_api_key", "claude_api_key"):
        if masked.get(key_field):
            masked[key_field] = mask_key(masked[key_field])
    return masked

@router.post("")
def update_settings(data: Dict[str, Any]):
    current = load_settings()
    # If key is masked or empty, preserve existing key
    for key_field in ("gemini_api_key", "openai_api_key", "claude_api_key"):
        new_val = data.get(key_field, "").strip()
        if not new_val or "..." in new_val:
            data[key_field] = current.get(key_field, "")
    save_settings(data)
    
    # Return masked
    masked = dict(data)
    for key_field in ("gemini_api_key", "openai_api_key", "claude_api_key"):
        if masked.get(key_field):
            masked[key_field] = mask_key(masked[key_field])
    return {"status": "saved", "settings": masked}

