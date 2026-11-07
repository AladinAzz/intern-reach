import json
import re
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.agent_reach import agent_reach_service, calculate_ats_affinity
from app.services.job_extractor import job_extractor, ExtractionError
from app.services.registries import profile_query
from app.services.storage import (
    load_profile,
    sanitize_job_dict,
    upsert_stored_jobs,
    are_jobs_duplicate,
)

router = APIRouter(prefix="/api/search", tags=["Search"])


class SearchRequest(BaseModel):
    query: Optional[str] = Field("", max_length=300)
    location: Optional[str] = Field("", max_length=120)


class ImportOfferRequest(BaseModel):
    url: Optional[str] = Field(None, max_length=2000)
    raw_text: Optional[str] = Field(None, max_length=30_000)


class SuggestKeywordsRequest(BaseModel):
    profile: Optional[Dict[str, Any]] = None


@router.post("")
async def search_internships(req: SearchRequest):
    # Empty query -> keywords derived from the CV profile (target domains, then skills).
    query = (req.query or "").strip() or profile_query()

    results = await agent_reach_service.search_internships_async(
        query=query,
        location=req.location or "",
    )
    return {
        "status": "success",
        "total": len(results),
        "location": req.location or "Toutes régions",
        "query": query or "Tous domaines",
        "results": results,
    }


@router.post("/import-offer")
async def import_offer(req: ImportOfferRequest):
    try:
        offer = await job_extractor.extract_from_url_or_text(url=req.url, raw_text=req.raw_text)
    except ExtractionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    offer = sanitize_job_dict(offer)
    stored = upsert_stored_jobs([offer])
    # Return the stored record (a duplicate of an already-known offer resolves to the existing entry/id).
    match = next((j for j in stored if j["id"] == offer["id"] or are_jobs_duplicate(offer, j)), offer)
    match = calculate_ats_affinity(dict(match), load_profile())
    return {"status": "success", "offer": match}


def _clean_str_list(value: Any, limit: int) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for v in value:
        s = str(v).strip() if v is not None else ""
        if s and s not in out:
            out.append(s[:100])
    return out[:limit]


@router.post("/suggest-keywords")
async def suggest_keywords(req: SuggestKeywordsRequest):
    """
    Analyses the CV profile with the configured LLM to propose the best search query, specialty facets and
    alternative search angles. Falls back to a deterministic derivation from the profile when the LLM is unavailable.
    """
    from app.services.letter_generator import letter_generator

    profile = req.profile if isinstance(req.profile, dict) and req.profile else load_profile()

    full_name = str(profile.get("full_name") or "Candidat")
    education = str(profile.get("education") or "")
    domains = _clean_str_list(profile.get("target_domains"), 10)
    skills = _clean_str_list(profile.get("technical_skills"), 30)
    projects = profile.get("key_projects") if isinstance(profile.get("key_projects"), list) else []
    proj_text = "; ".join(
        f"{p.get('title', '')}: {p.get('desc', '')}" for p in projects[:3] if isinstance(p, dict)
    )

    fallback_query = profile_query(profile)
    fallback = {
        "status": "success",
        "source": "profile",
        "suggested_query": fallback_query,
        "specialties": (domains or skills)[:5],
        "alternative_queries": [
            q for q in (
                {"label": "Domaines cibles", "query": ", ".join(domains[:3])} if domains else None,
                {"label": "Compétences clés", "query": ", ".join(skills[:3])} if skills else None,
                {"label": "Formation", "query": education[:60]} if education else None,
            ) if q
        ],
        "rationale": "Mots-clés dérivés directement de votre formation et de vos compétences (IA indisponible).",
    }

    if not (domains or skills or education or proj_text):
        raise HTTPException(status_code=422, detail="Profil vide : importez d'abord votre CV.")

    prompt = f"""Tu es un recruteur expert en France.
À partir du profil ci-dessous, génère la requête de recherche de stage la plus pertinente pour les moteurs d'emploi (LinkedIn, Indeed, Welcome to the Jungle).
N'invente aucune compétence absente du profil.

Profil du Candidat :
- Nom : {full_name}
- Formation : {education}
- Domaines Cibles : {', '.join(domains)}
- Compétences : {', '.join(skills)}
- Projets / expériences : {proj_text}

Consignes :
1. "suggested_query" : 2 à 3 expressions courtes séparées par des virgules (ex: "systèmes embarqués, traitement du signal").
2. "specialties" : 4 à 5 spécialités précises extraites du profil.
3. "alternative_queries" : 3 angles de recherche différents.
4. "rationale" : une phrase expliquant la stratégie.

Réponds UNIQUEMENT avec un JSON strict sans markdown :
{{
  "suggested_query": "...",
  "specialties": ["..."],
  "alternative_queries": [{{"label": "...", "query": "..."}}],
  "rationale": "..."
}}
"""
    try:
        ai_resp = await letter_generator.call_llm(prompt)
        if ai_resp:
            clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", ai_resp.strip(), flags=re.MULTILINE)
            match = re.search(r"\{.*\}", clean, re.DOTALL)
            data = json.loads(match.group(0) if match else clean)
            suggested = str(data.get("suggested_query") or "").strip()[:200] if isinstance(data, dict) else ""
            if suggested:
                alts = []
                for a in (data.get("alternative_queries") or [])[:5]:
                    if isinstance(a, dict) and str(a.get("query") or "").strip():
                        alts.append({"label": str(a.get("label") or "Angle")[:60], "query": str(a["query"]).strip()[:200]})
                return {
                    "status": "success",
                    "source": "ai",
                    "suggested_query": suggested,
                    "specialties": _clean_str_list(data.get("specialties"), 6) or fallback["specialties"],
                    "alternative_queries": alts,
                    "rationale": str(data.get("rationale") or "")[:300],
                }
    except Exception as e:
        print(f"Notice: AI keyword suggestion fallback: {type(e).__name__}: {e}")

    return fallback
