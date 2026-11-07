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

class SuggestKeywordsRequest(BaseModel):
    profile: Optional[Dict[str, Any]] = None

@router.post("/suggest-keywords")
async def suggest_keywords(req: SuggestKeywordsRequest):
    """
    Analyzes candidate's CV profile using AI to generate high-converting search queries,
    specialty facets, and strategic alternative search angles.
    """
    import re
    import json
    from app.services.storage import load_profile

    profile = req.profile or load_profile()

    full_name = profile.get("full_name", "Candidat")
    education = profile.get("education", "")
    domains = profile.get("target_domains", [])
    skills = profile.get("technical_skills", [])
    projects = profile.get("key_projects", [])

    proj_text = "; ".join([f"{p.get('title', '')}: {p.get('desc', '')}" for p in projects[:3]])

    fallback_suggested = ", ".join(domains[:3]) if domains else (", ".join(skills[:4]) if skills else "Stage Ingénierie R&D")
    fallback_specialties = domains if domains else skills[:5]

    prompt = f"""Tu es un recruteur technique expert en France.
À partir du CV et du profil ci-dessous, génère la requête de recherche de stage la plus percutante et optimisée pour les moteurs d'emploi (LinkedIn, Indeed, JobSpy, Welcome to the Jungle).

Profil du Candidat :
- Nom : {full_name}
- Formation : {education}
- Domaines Cibles : {', '.join(domains)}
- Compétences Techniques : {', '.join(skills)}
- Projets Clés : {proj_text}

Consignes :
1. "suggested_query" doit être concise (3 à 5 mots-clés réels) pour maximiser le taux de résultats pertinents.
2. "specialties" doit contenir 4 ou 5 spécialités / facettes précises extraites du CV.
3. "alternative_queries" doit proposer 3 angles différents (ex: R&D/Scientifique, Industriel/Grand Groupe, Startup/Tech Agile).
4. "rationale" explique brièvement en 1 phrase la stratégie de ciblage.

Réponds UNIQUEMENT avec un JSON strict sans markdown :
{{
  "suggested_query": "Requête principale (ex: Stage Systèmes Embarqués C++ FreeRTOS)",
  "specialties": ["Spécialité 1", "Spécialité 2", "Spécialité 3", "Spécialité 4"],
  "alternative_queries": [
    {{"label": "Angle R&D / Scientifique", "query": "requête ciblée"}},
    {{"label": "Angle Industrie / Grand Groupe", "query": "requête ciblée"}},
    {{"label": "Angle Compétences Clés", "query": "requête ciblée"}}
  ],
  "rationale": "Brève explication de la pertinence."
}}
"""
    try:
        from app.services.letter_generator import letter_generator
        ai_resp = await letter_generator.call_llm(prompt)
        if ai_resp:
            clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", ai_resp.strip(), flags=re.MULTILINE)
            data = json.loads(clean)
            if isinstance(data, dict) and "suggested_query" in data:
                return {
                    "status": "success",
                    **data
                }
    except Exception as e:
        print(f"Notice: AI keyword suggestion fallback: {e}")

    return {
        "status": "success",
        "suggested_query": fallback_suggested,
        "specialties": fallback_specialties or ["Ingénierie", "R&D", "Stage"],
        "alternative_queries": [
            {"label": "Domaines Cibles", "query": ", ".join(domains[:3]) if domains else "Stage Ingénierie"},
            {"label": "Compétences Clés", "query": ", ".join(skills[:3]) if skills else "C++ Python FreeRTOS"},
            {"label": "Formation Spécialisée", "query": f"Stage {education[:35]}" if education else "Stage Fin d'études"}
        ],
        "rationale": "Mots-clés optimisés directement depuis votre formation et vos compétences du CV."
    }

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

