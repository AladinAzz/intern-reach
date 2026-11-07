from typing import Dict, List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from app.services.cv_parser import (
    extract_text_from_pdf,
    parse_cv_with_ai,
    CvExtractionError,
    MIN_CV_CHARS,
)
from app.services.storage import load_profile, save_profile

router = APIRouter(prefix="/api/cv", tags=["CV"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class ProjectIn(BaseModel):
    title: str = Field("", max_length=300)
    desc: str = Field("", max_length=3000)


class ProfileIn(BaseModel):
    full_name: str = Field("", max_length=200)
    email: str = Field("", max_length=320)
    phone: str = Field("", max_length=60)
    education: str = Field("", max_length=500)
    target_domains: List[str] = Field(default_factory=list, max_length=50)
    technical_skills: List[str] = Field(default_factory=list, max_length=200)
    key_projects: List[ProjectIn] = Field(default_factory=list, max_length=50)
    raw_cv_text: Optional[str] = Field(None, max_length=200_000)


@router.get("/profile")
def get_profile():
    return load_profile()


@router.post("/profile")
def update_profile(profile: ProfileIn):
    data = profile.model_dump()
    if data.get("raw_cv_text") is None:
        # Keep the previously stored CV text when the client does not send it.
        data["raw_cv_text"] = load_profile().get("raw_cv_text", "")
    saved = save_profile(data)
    return {"status": "saved", "profile": saved}


@router.post("/upload")
async def upload_cv(file: UploadFile = File(...)):
    filename = (file.filename or "").lower()
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Fichier trop volumineux. La taille maximale autorisée est de 10 Mo.",
        )

    try:
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(content)
        elif filename.endswith(".txt") or filename.endswith(".md"):
            text = content.decode("utf-8", errors="ignore").strip()
            if len(text) < MIN_CV_CHARS:
                raise CvExtractionError("Le fichier est vide ou trop court pour être un CV.")
        else:
            raise HTTPException(status_code=400, detail="Format non supporté. Veuillez envoyer un PDF ou un fichier texte.")
    except CvExtractionError as e:
        raise HTTPException(status_code=422, detail=str(e))

    profile = await parse_cv_with_ai(text)
    saved = save_profile(profile)
    return {
        "status": "extracted",
        "filename": file.filename,
        "profile": saved,
    }
