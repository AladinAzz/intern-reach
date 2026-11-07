from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from app.services.letter_generator import letter_generator
from app.services.storage import load_profile

router = APIRouter(prefix="/api/letters", tags=["Letters"])

class GenerateRequest(BaseModel):
    job: Dict[str, Any]
    profile: Optional[Dict[str, Any]] = None

class RefineRequest(BaseModel):
    current_letter: str
    feedback: str
    job: Dict[str, Any]

@router.post("/generate")
async def generate_letters(req: GenerateRequest):
    profile = req.profile or load_profile()
    versions = await letter_generator.generate_versions(req.job, profile)
    return {
        "status": "success",
        "job_id": req.job.get("id"),
        "versions": versions
    }

@router.post("/refine")
async def refine_letter(req: RefineRequest):
    profile = load_profile()
    refined = await letter_generator.refine_letter(
        current_letter=req.current_letter,
        feedback=req.feedback,
        job=req.job,
        profile=profile
    )
    return {
        "status": "success",
        "refined_letter": refined
    }

class JobAnalysisRequest(BaseModel):
    job: Dict[str, Any]
    profile: Optional[Dict[str, Any]] = None

@router.post("/pitch-and-gap")
async def get_pitch_and_gap(req: JobAnalysisRequest):
    profile = req.profile or load_profile()
    data = await letter_generator.generate_pitches_and_gap_analysis(req.job, profile)
    return {
        "status": "success",
        "analysis": data
    }

@router.post("/interview-prep")
async def get_interview_prep(req: JobAnalysisRequest):
    profile = req.profile or load_profile()
    questions = await letter_generator.generate_interview_prep(req.job, profile)
    return {
        "status": "success",
        "questions": questions
    }

