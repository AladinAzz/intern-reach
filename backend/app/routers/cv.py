from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
from app.services.cv_parser import extract_text_from_pdf, parse_cv_to_profile
from app.services.storage import load_profile, save_profile

router = APIRouter(prefix="/api/cv", tags=["CV"])

@router.get("/profile")
def get_profile():
    return load_profile()

@router.post("/profile")
def update_profile(profile: Dict[str, Any]):
    save_profile(profile)
    return {"status": "saved", "profile": profile}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/upload")
async def upload_cv(file: UploadFile = File(...)):
    filename = file.filename.lower()
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Fichier trop volumineux. La taille maximale autorisée est de 10 Mo."
        )
    
    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(content)
    elif filename.endswith(".txt") or filename.endswith(".md"):
        text = content.decode("utf-8", errors="ignore")
    else:
        raise HTTPException(status_code=400, detail="Format non supporté. Veuillez envoyer un PDF ou un fichier texte.")
    
    profile = parse_cv_to_profile(text)
    return {
        "status": "extracted",
        "filename": file.filename,
        "profile": profile
    }

