import json
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

PROFILE_FILE = os.path.join(DATA_DIR, "profile.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
JOBS_FILE = os.path.join(DATA_DIR, "jobs.json")

class UserProfile(BaseModel):
    full_name: str = "Ingénieur Stagiaire"
    email: str = "etudiant@institution.edu"
    phone: str = "+33 6 00 00 00 00"
    education: str = "Master 2 / Dernière Année École d'Ingénieurs — Spécialité Systèmes Embarqués & IA"
    target_domains: List[str] = [
        "Systèmes Embarqués Temps Réel",
        "Edge AI & TinyML",
        "Traitement du Signal & Image",
        "Computer Vision",
        "Robotique & Perception"
    ]
    technical_skills: List[str] = [
        "C / C++ (C++17/20)",
        "Python (PyTorch, TorchVision)",
        "MATLAB / Simulink",
        "OpenCV",
        "Linux Embarqué / Yocto",
        "FreeRTOS / RTOS",
        "TensorRT / ONNX Runtime",
        "ROS 2",
        "VHDL / FPGA (Xilinx)",
        "Protocoles: SPI, I2C, CAN, UART"
    ]
    key_projects: List[Dict[str, str]] = [
        {
            "title": "Déploiement Edge AI de Segmentation Temps Réel",
            "desc": "Quantification INT8 et accélération sur carte NVIDIA Jetson Nano avec TensorRT (30 FPS soutenus)."
        },
        {
            "title": "Filtrage Numérique & Égalisation de Signal RF",
            "desc": "Conception sous MATLAB et implémentation en C++ d'un filtre adaptatif LMS avec rejet de bruit."
        },
        {
            "title": "Module de Navigation SLAM sous ROS 2",
            "desc": "Fusion de données centrale (LiDAR 2D + Centrale Inertielle IMU) avec filtrage de Kalman étendu (EKF)."
        }
    ]
    raw_cv_text: str = ""

def load_profile() -> Dict[str, Any]:
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    default = UserProfile().model_dump()
    save_profile(default)
    return default

def save_profile(data: Dict[str, Any]) -> None:
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_history() -> List[Dict[str, Any]]:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []

def save_history(history: List[Dict[str, Any]]) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def add_history_entry(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    history = load_history()
    entry_id = str(entry.get("id") or f"hist-{len(history)+1}")
    entry["id"] = entry_id
    
    # If already exists with same ID, replace in place
    replaced = False
    for i, h in enumerate(history):
        if str(h.get("id")) == entry_id:
            history[i] = entry
            replaced = True
            break
            
    if not replaced:
        # Prepend newest
        history.insert(0, entry)
        
    save_history(history)
    return history

def update_history_status(entry_id: str, new_status: str) -> List[Dict[str, Any]]:
    history = load_history()
    for h in history:
        if str(h.get("id")) == str(entry_id):
            h["status"] = new_status
            break
    save_history(history)
    return history

def delete_history_entry(entry_id: str) -> List[Dict[str, Any]]:
    history = load_history()
    history = [h for h in history if str(h.get("id")) != str(entry_id)]
    save_history(history)
    return history

def clear_history() -> List[Dict[str, Any]]:
    save_history([])
    return []

def load_settings() -> Dict[str, Any]:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "active_provider": "gemini",
        "gemini_api_key": "",
        "openai_api_key": "",
        "claude_api_key": "",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3:latest"
    }

def save_settings(data: Dict[str, Any]) -> None:
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def are_jobs_duplicate(job1: Dict[str, Any], job2: Dict[str, Any]) -> bool:
    """
    Determines whether two job postings are duplicates based on:
    1. Canonical URL equivalence (stripping tracking query params).
    2. Overlap of company name tokens + significant title tokens.
    """
    import re

    # 1. Direct URL comparison
    u1 = str(job1.get("url") or "").strip()
    u2 = str(job2.get("url") or "").strip()
    if u1 and u2 and "welcometothejungle.com" not in u1 and len(u1) > 15:
        clean1 = u1.split("?")[0].rstrip("/").lower()
        clean2 = u2.split("?")[0].rstrip("/").lower()
        if clean1 == clean2:
            return True

    # 2. Company comparison
    c1_raw = str(job1.get("company") or "").lower()
    c2_raw = str(job2.get("company") or "").lower()
    c1 = set(re.findall(r"\w+", c1_raw))
    c2 = set(re.findall(r"\w+", c2_raw))
    
    # Ignore generic filler company words
    company_stops = {"france", "sa", "sas", "sarl", "group", "groupe", "inc", "ltd"}
    c1_meaningful = c1 - company_stops
    c2_meaningful = c2 - company_stops
    
    if not (c1_meaningful & c2_meaningful):
        return False

    # 3. Title overlap comparison
    stops = {
        "stage", "internship", "stagiaire", "ingénieur", "ingenieur", "engineer",
        "intern", "f", "h", "m", "de", "du", "et", "en", "pour", "le", "la", "les", "un", "une", "d"
    }
    t1 = set(re.findall(r"\w+", str(job1.get("title") or "").lower())) - stops
    t2 = set(re.findall(r"\w+", str(job2.get("title") or "").lower())) - stops

    if not t1 or not t2:
        return False

    overlap = len(t1 & t2) / min(len(t1), len(t2))
    return overlap >= 0.65

def sanitize_job_dict(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cleanses any NaN or corrupted artifacts from scraped jobs, ensuring valid URLs and descriptions.
    """
    import urllib.parse
    title = str(job.get("title") or "").strip()
    company = str(job.get("company") or "").strip()
    location = str(job.get("location") or "France").strip()
    category = str(job.get("category") or "Ingénierie & R&D").strip()

    if title.lower() in ("nan", "none", "null", ""):
        title = "Stage Ingénieur R&D"
    if company.lower() in ("nan", "none", "null", ""):
        company = "Entreprise Recruteuse"
    if location.lower() in ("nan", "none", "null", ""):
        location = "France"

    # Sanitize URL
    url = str(job.get("url") or "").strip()
    if not url or url.lower() in ("nan", "none", "null") or not url.startswith("http"):
        search_query = f"Stage {title} {company} {location}".strip()
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}"

    # Sanitize Description
    desc = str(job.get("description") or "").strip()
    if not desc or desc.lower() in ("nan", "none", "null") or len(desc) < 20:
        desc = f"Opportunité de stage conventionné ({category}) chez {company} à {location}. Missions d'ingénierie, conception algorithmique et développement technique au sein de l'équipe."

    # Sanitize Date Posted
    from datetime import datetime
    date_posted = str(job.get("date_posted") or job.get("stored_at") or job.get("first_seen_at") or datetime.now().strftime("%Y-%m-%d"))[:10]
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}", date_posted):
        date_posted = datetime.now().strftime("%Y-%m-%d")

    job["title"] = title
    job["company"] = company
    job["location"] = location
    job["url"] = url
    job["description"] = desc
    job["date_posted"] = date_posted
    return job

def load_stored_jobs() -> List[Dict[str, Any]]:
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [sanitize_job_dict(j) for j in data if isinstance(j, dict)]
        except Exception as e:
            print(f"Notice: Erreur lecture jobs.json: {e}")
    return []

def save_stored_jobs(jobs: List[Dict[str, Any]]) -> None:
    try:
        clean_list = [sanitize_job_dict(j) for j in jobs if isinstance(j, dict)]
        with open(JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(clean_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Notice: Erreur écriture jobs.json: {e}")

def upsert_stored_jobs(new_jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Persists jobs to storage, merging duplicates and prepending fresh postings.
    Returns the complete list of unique stored jobs.
    """
    from datetime import datetime
    existing_jobs = load_stored_jobs()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    for raw_job in new_jobs:
        new_job = sanitize_job_dict(raw_job)
        matched_idx = -1
        for idx, exist in enumerate(existing_jobs):
            if are_jobs_duplicate(new_job, exist):
                matched_idx = idx
                break

        if matched_idx != -1:
            # Update existing with fresher data without duplicating
            existing = existing_jobs[matched_idx]
            for key in ("match_score", "matched_skills", "missing_skills", "source", "url", "date_posted"):
                if key in new_job and new_job[key] and str(new_job[key]).lower() != "nan":
                    existing[key] = new_job[key]
            existing["last_synced_at"] = now_str
        else:
            # Brand new job
            job_copy = dict(new_job)
            job_copy["stored_at"] = now_str
            job_copy["first_seen_at"] = now_str
            existing_jobs.insert(0, job_copy)

    save_stored_jobs(existing_jobs)
    return existing_jobs

