import os
from pydantic import BaseModel
from typing import Optional

class AppSettings(BaseModel):
    # LLM BYOK (Bring Your Own Key) Settings
    active_provider: str = "gemini"  # "gemini" | "openai" | "claude" | "ollama" | "mock"
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    claude_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY", "")
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3:latest"
    
    # Search & Location Defaults
    default_location: str = "Paris, Île-de-France"
    default_query: str = "Systèmes embarqués, Edge AI, Traitement du signal / image"
    agent_reach_enabled: bool = True

settings = AppSettings()

