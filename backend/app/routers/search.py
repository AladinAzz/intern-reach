from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.agent_reach import agent_reach_service
from app.services.job_extractor import job_extractor

router = APIRouter(prefix="/api/search", tags=["Search"])

class SearchRequest(BaseModel):
    query: Optional[str] = "Systèmes embarqués, Edge AI, Traitement du signal"
    location: Optional[str] = "Paris, Île-de-France"

class ImportOfferRequest(BaseModel):
    url: Optional[str] = None
    raw_text: Optional[str] = None

@router.post("")
def search_internships(req: SearchRequest):
    results = agent_reach_service.search_internships(
        query=req.query or "",
        location=req.location or "Paris, Île-de-France"
    )
    return {
        "status": "success",
        "total": len(results),
        "location": req.location,
        "query": req.query,
        "results": results
    }

@router.post("/import-offer")
async def import_offer(req: ImportOfferRequest):
    offer = await job_extractor.extract_from_url_or_text(url=req.url, raw_text=req.raw_text)
    return {
        "status": "success",
        "offer": offer
    }

