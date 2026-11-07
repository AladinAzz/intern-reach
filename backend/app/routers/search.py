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
    results = await agent_reach_service.search_internships_async(
        query=req.query or "",
        location=req.location or ""
    )
    return {
        "status": "success",
        "total": len(results),
        "location": req.location or "Toutes régions",
        "query": req.query or "Tous domaines",
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

