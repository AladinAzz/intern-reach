import json
import os
import re
import tempfile
import threading
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from pydantic import BaseModel, Field

# The data directory can be overridden (used by the test-suite so that tests never touch real user data).
DATA_DIR = os.environ.get("INTERN_REACH_DATA_DIR") or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

PROFILE_FILE = os.path.join(DATA_DIR, "profile.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
JOBS_FILE = os.path.join(DATA_DIR, "jobs.json")

# Single re-entrant lock serialising every read-modify-write cycle on the JSON stores
# (HTTP handlers run in a threadpool and the ingestion worker writes concurrently).
STORE_LOCK = threading.RLock()

HISTORY_STATUSES = ("Enregistré", "Candidaté", "Entretien", "Accepté", "Refusé")
LLM_PROVIDERS = ("gemini", "openai", "claude", "ollama", "mock")


def atomic_write_json(path: str, data: Any) -> None:
    """Write JSON atomically (temp file + os.replace) so a crash never leaves a truncated store."""
    directory = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def read_json(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Notice: unreadable store {os.path.basename(path)}: {e}")
        return default


class UserProfile(BaseModel):
    """Candidate profile. Defaults are intentionally empty: everything comes from the uploaded CV."""
    full_name: str = ""
    email: str = ""
    phone: str = ""
    education: str = ""
    target_domains: List[str] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    key_projects: List[Dict[str, str]] = Field(default_factory=list)
    raw_cv_text: str = ""


def _str_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for item in value:
        s = str(item).strip() if item is not None else ""
        if s and s not in out:
            out.append(s)
    return out


def normalize_profile(data: Any) -> Dict[str, Any]:
    """Coerce arbitrary input into a well-formed profile dict (never raises, never drops required keys)."""
    base = UserProfile().model_dump()
    if not isinstance(data, dict):
        return base
    for key in ("full_name", "email", "phone", "education", "raw_cv_text"):
        val = data.get(key)
        text = "" if val is None else str(val)
        base[key] = text if key == "raw_cv_text" else text.strip()
    base["target_domains"] = _str_list(data.get("target_domains"))
    base["technical_skills"] = _str_list(data.get("technical_skills"))
    projects: List[Dict[str, str]] = []
    raw_projects = data.get("key_projects")
    if isinstance(raw_projects, list):
        for p in raw_projects:
            if isinstance(p, dict):
                title = str(p.get("title") or "").strip()
                desc = str(p.get("desc") or "").strip()
                if title or desc:
                    projects.append({"title": title, "desc": desc})
            elif isinstance(p, str) and p.strip():
                projects.append({"title": p.strip(), "desc": ""})
    base["key_projects"] = projects
    return base


def load_profile() -> Dict[str, Any]:
    with STORE_LOCK:
        return normalize_profile(read_json(PROFILE_FILE, {}))


def save_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    clean = normalize_profile(data)
    with STORE_LOCK:
        atomic_write_json(PROFILE_FILE, clean)
    return clean


def load_history() -> List[Dict[str, Any]]:
    with STORE_LOCK:
        data = read_json(HISTORY_FILE, [])
    return [h for h in data if isinstance(h, dict)] if isinstance(data, list) else []


def save_history(history: List[Dict[str, Any]]) -> None:
    with STORE_LOCK:
        atomic_write_json(HISTORY_FILE, history)


def add_history_entry(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    with STORE_LOCK:
        history = load_history()
        entry = dict(entry)
        entry_id = str(entry.get("id") or f"hist-{uuid.uuid4().hex[:12]}")
        entry["id"] = entry_id
        status = entry.get("status")
        if status not in HISTORY_STATUSES:
            entry["status"] = "Enregistré"

        for i, h in enumerate(history):
            if str(h.get("id")) == entry_id:
                history[i] = entry
                break
        else:
            history.insert(0, entry)  # newest first

        save_history(history)
        return history


def update_history_status(entry_id: str, new_status: str) -> Optional[List[Dict[str, Any]]]:
    """Returns the updated history, or None when the entry does not exist."""
    with STORE_LOCK:
        history = load_history()
        found = False
        for h in history:
            if str(h.get("id")) == str(entry_id):
                h["status"] = new_status
                found = True
                break
        if not found:
            return None
        save_history(history)
        return history


def delete_history_entry(entry_id: str) -> Optional[List[Dict[str, Any]]]:
    """Returns the updated history, or None when the entry does not exist."""
    with STORE_LOCK:
        history = load_history()
        remaining = [h for h in history if str(h.get("id")) != str(entry_id)]
        if len(remaining) == len(history):
            return None
        save_history(remaining)
        return remaining


def clear_history() -> List[Dict[str, Any]]:
    save_history([])
    return []


DEFAULT_SETTINGS: Dict[str, Any] = {
    "active_provider": "gemini",
    "gemini_api_key": "",
    "openai_api_key": "",
    "claude_api_key": "",
    "ollama_base_url": "http://localhost:11434",
    "ollama_model": "llama3:latest",
}


_ENV_KEYS = {
    "gemini_api_key": "GEMINI_API_KEY",
    "openai_api_key": "OPENAI_API_KEY",
    "claude_api_key": "ANTHROPIC_API_KEY",
}


def load_settings() -> Dict[str, Any]:
    with STORE_LOCK:
        data = read_json(SETTINGS_FILE, {})
    merged = dict(DEFAULT_SETTINGS)
    if isinstance(data, dict):
        merged.update({k: v for k, v in data.items() if v is not None})
    # API keys may also come from the environment (e.g. backend/.env loaded by the shell); the file wins.
    for field, env_name in _ENV_KEYS.items():
        if not merged.get(field) and os.environ.get(env_name):
            merged[field] = os.environ[env_name]
    return merged


def save_settings(data: Dict[str, Any]) -> None:
    with STORE_LOCK:
        atomic_write_json(SETTINGS_FILE, data)


# ---------------------------------------------------------------------------
# Job store & de-duplication
# ---------------------------------------------------------------------------

# Query parameters that carry tracking noise only (never job identity such as Indeed's ``jk`` / ``vjk``).
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "trk", "trackingid",
    "refid", "ref", "referer", "referrer", "source", "src", "from", "fbclid", "gclid", "lipi",
    "midtoken", "midsig", "trkemail", "eid", "otptoken", "position", "pagenum",
}


def canonical_url(url: str) -> str:
    """Normalises a job URL for equality checks: drops fragments and tracking params but keeps identity params."""
    url = str(url or "").strip()
    if not url:
        return ""
    try:
        p = urlparse(url)
        kept = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=False) if k.lower() not in _TRACKING_PARAMS]
        kept.sort()
        path = p.path.rstrip("/")
        return urlunparse((p.scheme.lower(), p.netloc.lower().removeprefix("www."), path, "", urlencode(kept), ""))
    except Exception:
        return url.split("#")[0].rstrip("/").lower()


def stable_job_id(job: Dict[str, Any]) -> str:
    """Deterministic id derived from the canonical URL (or title+company) – stable across runs/processes."""
    import hashlib
    basis = canonical_url(job.get("url", "")) or f"{job.get('title', '')}|{job.get('company', '')}|{job.get('location', '')}"
    return "job-" + hashlib.sha1(basis.lower().encode("utf-8")).hexdigest()[:14]


_GENERIC_COMPANIES = {"entreprise", "innovante", "recruteuse", "non", "précisée", "precisee", "france", "sa", "sas", "sarl", "group", "groupe", "inc", "ltd", "the", "de", "des", "du", "la", "le"}
_GENERIC_LOCATIONS = {"france", "région", "region", "remote", "télétravail", "teletravail", "europe", ""}


def _tokens(text: str) -> set:
    return set(re.findall(r"\w+", str(text or "").lower()))


def are_jobs_duplicate(job1: Dict[str, Any], job2: Dict[str, Any]) -> bool:
    """
    Two postings are duplicates when:
    1. their canonical URLs are identical, or
    2. they share a meaningful company token, have near-identical titles and compatible locations.
    """
    u1 = canonical_url(job1.get("url", ""))
    u2 = canonical_url(job2.get("url", ""))
    if u1 and u2 and len(u1) > 15 and u1 == u2:
        return True

    c1 = _tokens(job1.get("company")) - _GENERIC_COMPANIES
    c2 = _tokens(job2.get("company")) - _GENERIC_COMPANIES
    if not (c1 & c2):
        return False

    title_stops = {
        "stage", "internship", "stagiaire", "ingénieur", "ingenieur", "ingénieure", "engineer", "intern",
        "f", "h", "m", "e", "de", "du", "et", "en", "pour", "le", "la", "les", "un", "une", "d", "mois", "pfe",
    }
    t1 = _tokens(job1.get("title")) - title_stops
    t2 = _tokens(job2.get("title")) - title_stops
    if not t1 or not t2:
        return False
    if len(t1 & t2) / max(len(t1), len(t2)) < 0.75:
        return False

    l1 = _tokens(job1.get("location")) - _GENERIC_LOCATIONS
    l2 = _tokens(job2.get("location")) - _GENERIC_LOCATIONS
    if l1 and l2 and not (l1 & l2):
        return False  # same company/title in two different cities = two distinct offers
    return True


_NAN_VALUES = ("nan", "none", "null", "<na>", "undefined", "")


def is_blank(value: Any) -> bool:
    return value is None or str(value).strip().lower() in _NAN_VALUES


def sanitize_job_dict(job: Dict[str, Any]) -> Dict[str, Any]:
    """Cleanses NaN/corrupted artifacts and guarantees the shape the frontend relies on."""
    import urllib.parse

    title = str(job.get("title") or "").strip()
    company = str(job.get("company") or "").strip()
    location = str(job.get("location") or "").strip()
    category = str(job.get("category") or "").strip()

    if is_blank(title):
        title = "Stage (intitulé non précisé)"
    if is_blank(company):
        company = "Entreprise non précisée"
    if is_blank(location):
        location = "France"
    if is_blank(category):
        category = "Stage"

    url = str(job.get("url") or "").strip()
    if is_blank(url) or not re.match(r"^https?://", url, re.IGNORECASE):
        search_query = f"Stage {title} {company} {location}".strip()
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}"

    desc = str(job.get("description") or "").strip()
    if is_blank(desc) or len(desc) < 20:
        desc = f"Offre de stage « {title} » chez {company} ({location}). Consultez l'offre source pour le détail des missions."

    date_posted = str(job.get("date_posted") or "")[:10]
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_posted):
        job.setdefault("date_estimated", False)
    else:
        # No reliable publication date (web-search results): fall back to the first time we saw the offer
        # and flag it so the UI can say "détectée le" instead of claiming a publication date.
        seen = str(job.get("first_seen_at") or job.get("stored_at") or "")[:10]
        date_posted = seen if re.match(r"^\d{4}-\d{2}-\d{2}$", seen) else datetime.now().strftime("%Y-%m-%d")
        job["date_estimated"] = True

    tags = job.get("tags")
    tags = [str(t).strip() for t in tags if str(t).strip()] if isinstance(tags, list) else []

    job["title"] = title
    job["company"] = company
    job["location"] = location
    job["category"] = category
    job["url"] = url
    job["description"] = desc
    job["date_posted"] = date_posted
    job["tags"] = tags
    job["contract"] = str(job.get("contract") or "Stage")
    job["recruiter_type"] = str(job.get("recruiter_type") or "")
    job["recruiter_profile"] = str(job.get("recruiter_profile") or "")
    try:
        job["match_score"] = int(job.get("match_score") or 0)
    except (TypeError, ValueError):
        job["match_score"] = 0
    # Stable identifier (the previous index-based ids collided between searches).
    job["id"] = stable_job_id(job)
    return job


def load_stored_jobs() -> List[Dict[str, Any]]:
    with STORE_LOCK:
        data = read_json(JOBS_FILE, [])
    if isinstance(data, list):
        return [sanitize_job_dict(j) for j in data if isinstance(j, dict)]
    return []


def save_stored_jobs(jobs: List[Dict[str, Any]]) -> None:
    clean_list = [sanitize_job_dict(j) for j in jobs if isinstance(j, dict)]
    with STORE_LOCK:
        atomic_write_json(JOBS_FILE, clean_list)


def upsert_stored_jobs(new_jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Persists jobs to storage, merging duplicates and prepending fresh postings.
    Returns the complete list of unique stored jobs.
    """
    with STORE_LOCK:
        existing_jobs = load_stored_jobs()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        for raw_job in new_jobs:
            if not isinstance(raw_job, dict):
                continue
            new_job = sanitize_job_dict(dict(raw_job))
            matched_idx = -1
            for idx, exist in enumerate(existing_jobs):
                if are_jobs_duplicate(new_job, exist):
                    matched_idx = idx
                    break

            if matched_idx != -1:
                existing = existing_jobs[matched_idx]
                if not is_blank(new_job.get("source")):
                    existing["source"] = new_job["source"]
                # A real publication date always wins over an estimate; an estimate never moves an existing date.
                if not new_job.get("date_estimated"):
                    existing["date_posted"] = new_job["date_posted"]
                    existing["date_estimated"] = False
                # Only trust a fresher description when it is a real one (not the generic placeholder).
                if len(new_job.get("description", "")) > len(existing.get("description", "")) and "Consultez l'offre source" not in new_job["description"]:
                    existing["description"] = new_job["description"]
                if new_job.get("tags") and not existing.get("tags"):
                    existing["tags"] = new_job["tags"]
                existing["last_synced_at"] = now_str
            else:
                job_copy = dict(new_job)
                job_copy.setdefault("stored_at", now_str)
                job_copy.setdefault("first_seen_at", now_str)
                existing_jobs.insert(0, job_copy)

        save_stored_jobs(existing_jobs)
        return existing_jobs


def update_jobs_liveness(results: Dict[str, Optional[bool]], checked_at: str) -> List[Dict[str, Any]]:
    """
    Applies liveness verdicts (job id -> True/False/None) onto the *current* store under the lock, so verdicts
    computed during a long network sweep never clobber jobs added concurrently. ``None`` = inconclusive (unchanged).
    """
    with STORE_LOCK:
        jobs = load_stored_jobs()
        for job in jobs:
            if job["id"] in results:
                verdict = results[job["id"]]
                if verdict is not None:
                    job["is_active"] = verdict
                job["last_checked"] = checked_at
        save_stored_jobs(jobs)
        return jobs
