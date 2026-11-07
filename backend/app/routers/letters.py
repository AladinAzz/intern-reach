from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.letter_generator import letter_generator, LLMError
from app.services.storage import load_profile, normalize_profile

router = APIRouter(prefix="/api/letters", tags=["Letters"])


class JobIn(BaseModel):
    """Offer context. Extra keys (id, tags, category...) are accepted and forwarded."""
    model_config = ConfigDict(extra="allow")

    title: str = Field(..., min_length=1, max_length=500)
    company: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = Field(None, max_length=20_000)

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        return v


def _job_dict(job: JobIn) -> Dict[str, Any]:
    return job.model_dump()


def _profile(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return normalize_profile(raw) if isinstance(raw, dict) and raw else load_profile()


class GenerateRequest(BaseModel):
    job: JobIn
    profile: Optional[Dict[str, Any]] = None


class RefineRequest(BaseModel):
    current_letter: str = Field(..., min_length=1, max_length=50_000)
    feedback: str = Field(..., min_length=1, max_length=2_000)
    job: JobIn


class JobAnalysisRequest(BaseModel):
    job: JobIn
    profile: Optional[Dict[str, Any]] = None


@router.post("/generate")
async def generate_letters(req: GenerateRequest):
    job = _job_dict(req.job)
    versions = await letter_generator.generate_versions(job, _profile(req.profile))
    return {
        "status": "success",
        "job_id": job.get("id"),
        "versions": versions,
        "ai_used": any(v.get("generated_by") == "ai" for v in versions),
    }


@router.post("/refine")
async def refine_letter(req: RefineRequest):
    try:
        refined = await letter_generator.refine_letter(
            current_letter=req.current_letter,
            feedback=req.feedback,
            job=_job_dict(req.job),
            profile=load_profile(),
        )
    except LLMError as e:
        raise HTTPException(status_code=503, detail=f"Révision impossible : {e}")
    return {"status": "success", "refined_letter": refined}


@router.post("/pitch-and-gap")
async def get_pitch_and_gap(req: JobAnalysisRequest):
    data = await letter_generator.generate_pitches_and_gap_analysis(_job_dict(req.job), _profile(req.profile))
    return {"status": "success", "analysis": data}


@router.post("/interview-prep")
async def get_interview_prep(req: JobAnalysisRequest):
    questions = await letter_generator.generate_interview_prep(_job_dict(req.job), _profile(req.profile))
    return {"status": "success", "questions": questions}
