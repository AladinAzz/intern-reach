from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.agent_reach import agent_reach_service
from app.services.job_extractor import job_extractor

router = APIRouter(prefix="/api/search", tags=["Search"])

class SearchRequest(BaseModel):
    query: Optional[str] = ""
    location: Optional[str] = ""

class ImportOfferRequest(BaseModel):
    url: Optional[str] = None
    raw_text: Optional[str] = None

@router.post("")
async def search_internships(req: SearchRequest):
    query = (req.query or "").strip()
    
    # If no query passed, dynamically derive keywords & specialties from stored CV profile
    if not query:
        from app.services.storage import load_profile
        profile = load_profile()
        target_domains = profile.get("target_domains", [])
        technical_skills = profile.get("technical_skills", [])
        
        if target_domains:
            query = ", ".join(target_domains[:3])
        elif technical_skills:
            query = ", ".join(technical_skills[:4])

    results = await agent_reach_service.search_internships_async(
        query=query,
        location=req.location or ""
    )
    return {
        "status": "success",
        "total": len(results),
        "location": req.location or "Toutes régions",
        "query": query or "Mots-clés CV",
        "results": results
    }

@router.post("/import-offer")
async def import_offer(req: ImportOfferRequest):
    offer = await job_extractor.extract_from_url_or_text(url=req.url, raw_text=req.raw_text)
    if offer and isinstance(offer, dict):
        from app.services.storage import upsert_stored_jobs
        upsert_stored_jobs([offer])
    return {
        "status": "success",
        "offer": offer
    }

