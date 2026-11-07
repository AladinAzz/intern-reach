import json
import os

import pytest
from fastapi.testclient import TestClient

from main import app
from app.services import agent_reach
from app.services.storage import DATA_DIR, load_stored_jobs, save_profile

client = TestClient(app)
PROFILE_PDF = os.path.join(os.path.dirname(__file__), "Profile.pdf")

PROFILE = {
    "full_name": "Ada Lovelace",
    "email": "ada@example.org",
    "phone": "+33 6 11 22 33 44",
    "education": "Master Mathématiques appliquées",
    "target_domains": ["Calcul scientifique", "Algorithmique"],
    "technical_skills": ["Python", "C++"],
    "key_projects": [{"title": "Moteur analytique", "desc": "Simulation numérique"}],
}
JOB = {"id": "j1", "title": "Stage Algorithmique", "company": "Babbage Labs", "category": "Algo",
       "description": "Python et C++ pour du calcul", "tags": ["Python", "Rust"], "location": "Paris"}


def test_health():
    assert client.get("/health").json()["status"] == "healthy"


# ----------------------------------------------------------------------------- CORS / hardening
def test_cors_only_allows_local_frontend():
    ok = client.options("/api/search", headers={"Origin": "http://localhost:3005", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3005"
    bad = client.options("/api/search", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"})
    assert bad.headers.get("access-control-allow-origin") is None


# ----------------------------------------------------------------------------- CV
def test_profile_roundtrip_and_validation():
    assert client.get("/api/cv/profile").json()["technical_skills"] == []
    r = client.post("/api/cv/profile", json=PROFILE)
    assert r.status_code == 200 and r.json()["profile"]["full_name"] == "Ada Lovelace"
    assert client.get("/api/cv/profile").json()["technical_skills"] == ["Python", "C++"]
    assert client.post("/api/cv/profile", json=["not", "a", "dict"]).status_code == 422
    assert client.post("/api/cv/profile", json={"technical_skills": "oops"}).status_code == 422
    assert client.post("/api/cv/profile", json={"full_name": "x" * 500}).status_code == 422


def test_upload_txt_replaces_profile_cleanly(no_llm):
    save_profile({**PROFILE})
    cv = "Marie Curie\nmarie@lab.fr\nCompétences\nRadioactivité\nChimie\nExpérience\nLaboratoire de physique"
    r = client.post("/api/cv/upload", files={"file": ("cv.txt", cv.encode(), "text/plain")})
    assert r.status_code == 200
    p = r.json()["profile"]
    assert p["full_name"] == "Marie Curie" and p["technical_skills"] == ["Radioactivité", "Chimie"]
    assert p["key_projects"] == [] and p["target_domains"] == []  # nothing leaked from the previous CV
    assert client.get("/api/cv/profile").json() == p


def test_upload_real_pdf_regex_fallback(no_llm):
    with open(PROFILE_PDF, "rb") as f:
        r = client.post("/api/cv/upload", files={"file": ("Profile.pdf", f, "application/pdf")})
    assert r.status_code == 200
    p = r.json()["profile"]
    assert "@" in p["email"] and p["raw_cv_text"]


def test_upload_bad_files_are_rejected_without_touching_profile():
    save_profile({**PROFILE})
    before = client.get("/api/cv/profile").json()
    assert client.post("/api/cv/upload", files={"file": ("bad.pdf", b"%PDF-1.4 garbage", "application/pdf")}).status_code == 422
    assert client.post("/api/cv/upload", files={"file": ("empty.txt", b"", "text/plain")}).status_code == 422
    assert client.post("/api/cv/upload", files={"file": ("tiny.txt", b"hi", "text/plain")}).status_code == 422
    assert client.post("/api/cv/upload", files={"file": ("x.exe", b"MZ" * 40, "application/octet-stream")}).status_code == 400
    assert client.get("/api/cv/profile").json() == before


def test_upload_file_size_limit():
    oversized = b"0" * (10 * 1024 * 1024 + 100)
    r = client.post("/api/cv/upload", files={"file": ("big_cv.txt", oversized, "text/plain")})
    assert r.status_code == 413 and "volumineux" in r.json()["detail"]


# ----------------------------------------------------------------------------- search
def _stub_live(monkeypatch, jobs):
    async def fake(query, location):
        fake.last = (query, location)
        return [dict(j) for j in jobs]
    monkeypatch.setattr(agent_reach, "execute_live_search_tools", fake)
    return fake


def test_search_uses_cv_keywords_when_query_empty(monkeypatch):
    save_profile({**PROFILE})
    fake = _stub_live(monkeypatch, [{"title": "Stage Calcul", "company": "Z", "url": "https://z.org/jobs/zzzzzzzz", "description": "calcul scientifique " * 3}])
    r = client.post("/api/search", json={"query": "", "location": ""})
    assert r.status_code == 200
    assert fake.last[0] == "Calcul scientifique, Algorithmique"
    assert r.json()["total"] == 1


def test_search_input_validation_and_nulls(monkeypatch):
    _stub_live(monkeypatch, [])
    assert client.post("/api/search", json={"query": None, "location": None}).status_code == 200
    assert client.post("/api/search", json={}).status_code == 200
    assert client.post("/api/search", json={"query": "x" * 5000}).status_code == 422


def test_search_results_have_no_nan_and_valid_urls(monkeypatch):
    _stub_live(monkeypatch, [{"title": "Stage A", "company": "nan", "url": "nan", "description": "nan", "date_posted": "nan"}])
    res = client.post("/api/search", json={"query": "stage"}).json()["results"]
    assert res and all(j["url"].startswith("http") for j in res)
    assert all("nan" not in (j["description"].lower().split()) for j in res)


def test_import_offer_errors_and_ssrf():
    assert client.post("/api/search/import-offer", json={}).status_code == 422
    n0 = len(load_stored_jobs())
    for url in ("http://127.0.0.1:8008/api/settings", "http://localhost:8008/health", "http://169.254.169.254/latest/meta-data/",
                "http://[::1]:8008/health", "http://0.0.0.0:8008/health", "file:///etc/passwd", "ftp://x"):
        r = client.post("/api/search/import-offer", json={"url": url})
        assert r.status_code == 400, url
    assert len(load_stored_jobs()) == n0  # blocked imports are never persisted


def test_import_offer_from_text_is_stored_and_stable(fake_llm):
    fake_llm.reply = json.dumps({"title": "Stage FPGA", "company": "Thales", "location": "Toulouse", "tags": ["VHDL"], "description": "Conception FPGA et validation"})
    r = client.post("/api/search/import-offer", json={"raw_text": "Stage FPGA chez Thales à Toulouse " * 3})
    assert r.status_code == 200
    offer = r.json()["offer"]
    assert offer["company"] == "Thales" and offer["id"].startswith("job-") and offer["url"].startswith("http")
    r2 = client.post("/api/search/import-offer", json={"raw_text": "Stage FPGA chez Thales à Toulouse " * 3})
    assert r2.json()["offer"]["id"] == offer["id"]
    assert len(load_stored_jobs()) == 1


def test_suggest_keywords_ai_and_fallback(fake_llm, no_llm):
    # no LLM: deterministic derivation from the profile
    r = client.post("/api/search/suggest-keywords", json={"profile": PROFILE})
    d = r.json()
    assert r.status_code == 200 and d["source"] == "profile" and d["suggested_query"] == "Calcul scientifique, Algorithmique"
    # empty profile -> clear 422 (nothing to analyse)
    assert client.post("/api/search/suggest-keywords", json={}).status_code == 422


def test_suggest_keywords_with_ai(fake_llm):
    fake_llm.reply = '```json\n{"suggested_query":"calcul scientifique, HPC","specialties":["HPC","Algo"],"alternative_queries":[{"label":"R&D","query":"stage R&D calcul"}],"rationale":"ok"}\n```'
    d = client.post("/api/search/suggest-keywords", json={"profile": PROFILE}).json()
    assert d["source"] == "ai" and d["suggested_query"] == "calcul scientifique, HPC" and d["alternative_queries"][0]["query"] == "stage R&D calcul"
    fake_llm.reply = "pas du json"
    assert client.post("/api/search/suggest-keywords", json={"profile": PROFILE}).json()["source"] == "profile"


# ----------------------------------------------------------------------------- letters
def test_generate_letters_template_is_grounded_in_profile(no_llm):
    save_profile({**PROFILE})
    r = client.post("/api/letters/generate", json={"job": JOB})
    assert r.status_code == 200
    d = r.json()
    assert d["ai_used"] is False and len(d["versions"]) == 3
    for v in d["versions"]:
        assert v["generated_by"] == "template" and "Ada Lovelace" in v["content"] and "Babbage Labs" in v["content"]
        assert "C++" in v["content"] or "Python" in v["content"]
        assert "Jetson" not in v["content"] and "FreeRTOS" not in v["content"]  # no invented embedded-systems claims
        assert 0 <= v["match_percentage"] <= 99


def test_generate_letters_works_with_empty_profile_and_sparse_job(no_llm):
    r = client.post("/api/letters/generate", json={"job": {"title": "Stage", "tags": None, "company": None, "description": None}, "profile": {"key_projects": []}})
    assert r.status_code == 200 and len(r.json()["versions"]) == 3


def test_generate_letters_with_ai(fake_llm):
    fake_llm.reply = "Madame, Monsieur, ... lettre IA"
    d = client.post("/api/letters/generate", json={"job": JOB, "profile": PROFILE}).json()
    assert d["ai_used"] is True and all(v["content"].startswith("Madame") for v in d["versions"])


def test_letters_validation():
    assert client.post("/api/letters/generate", json={}).status_code == 422
    assert client.post("/api/letters/generate", json={"job": {"title": "  "}}).status_code == 422
    assert client.post("/api/letters/refine", json={"current_letter": "", "feedback": "x", "job": JOB}).status_code == 422


def test_refine_never_corrupts_letter_when_llm_down(no_llm):
    r = client.post("/api/letters/refine", json={"current_letter": "Bonjour", "feedback": "plus court", "job": JOB})
    assert r.status_code == 503 and "Révision impossible" in r.json()["detail"]


def test_refine_with_ai(fake_llm):
    fake_llm.reply = "Lettre raccourcie"
    r = client.post("/api/letters/refine", json={"current_letter": "Bonjour", "feedback": "plus court", "job": JOB})
    assert r.status_code == 200 and r.json()["refined_letter"] == "Lettre raccourcie"


def test_pitch_and_gap(no_llm, fake_llm):
    save_profile({**PROFILE})
    d = client.post("/api/letters/pitch-and-gap", json={"job": JOB}).json()["analysis"]
    assert d["matched_skills"] == ["Python"] and d["missing_skills"] == ["Rust"]
    for k in ("cold_email_subject", "cold_email_body", "linkedin_note", "bridge_advice"):
        assert d[k]
    fake_llm.reply = json.dumps({"cold_email_subject": "S", "cold_email_body": "B", "linkedin_note": "L" * 400, "bridge_advice": "A"})
    d = client.post("/api/letters/pitch-and-gap", json={"job": JOB}).json()["analysis"]
    assert d["generated_by"] == "ai" and len(d["linkedin_note"]) == 300


def test_interview_prep(no_llm, fake_llm):
    r = client.post("/api/letters/interview-prep", json={"job": {**JOB, "tags": []}})
    assert r.status_code == 200 and 3 <= len(r.json()["questions"]) <= 5
    fake_llm.reply = json.dumps([{"question": f"Q{i}", "expected_answer": "a", "tip": "t"} for i in range(7)])
    qs = client.post("/api/letters/interview-prep", json={"job": JOB}).json()["questions"]
    assert len(qs) == 5 and qs[0]["question"] == "Q0"


# ----------------------------------------------------------------------------- history
def test_history_lifecycle():
    base = {"job_title": "T", "company": "C", "location": "L", "url": "https://x.org", "applied_at": "2026-11-07",
            "status": "Enregistré", "selected_version": "v1", "letter_content": "x"}
    r = client.post("/api/history", json={**base, "id": "fixed"})
    assert r.status_code == 200
    ids = [client.post("/api/history", json=base).json()["history"][0]["id"] for _ in range(3)]
    assert len(set(ids)) == 3  # no id collisions
    assert client.patch("/api/history/fixed/status", json={"status": "Entretien"}).json()["history"][-1]["status"] in ("Entretien",)
    assert client.patch("/api/history/missing/status", json={"status": "Entretien"}).status_code == 404
    assert client.patch("/api/history/fixed/status", json={"status": "HACKED"}).status_code == 422
    assert client.delete("/api/history/missing").status_code == 404
    assert client.delete("/api/history/fixed").status_code == 200
    assert client.put("/api/history", json="oops").status_code == 422
    assert client.post("/api/history", json={**base, "status": "nope"}).status_code == 422
    assert client.delete("/api/history").json()["history"] == []


# ----------------------------------------------------------------------------- settings
def test_settings_masking_and_validation():
    r = client.post("/api/settings", json={"active_provider": "gemini", "gemini_api_key": "AIzaSyABCDEFGHIJKLMNOP"})
    assert r.status_code == 200 and "..." in r.json()["settings"]["gemini_api_key"]
    got = client.get("/api/settings").json()
    assert got["gemini_api_key"] == "AIza...MNOP" and "ABCDEFGH" not in json.dumps(got)
    # re-saving with the masked value (or null / empty) must keep the real secret
    for val in (got["gemini_api_key"], None, ""):
        assert client.post("/api/settings", json={"active_provider": "gemini", "gemini_api_key": val}).status_code == 200
        with open(os.path.join(DATA_DIR, "settings.json"), encoding="utf-8") as f:
            assert json.load(f)["gemini_api_key"] == "AIzaSyABCDEFGHIJKLMNOP"
    assert client.post("/api/settings", json={"active_provider": "evil"}).status_code == 422
    assert client.post("/api/settings", json={"active_provider": "gemini", "openai_api_key": "sk-short"}).json()["settings"]["openai_api_key"] == "...rt"


# ----------------------------------------------------------------------------- worker
def test_worker_settings_validation():
    s = client.get("/api/worker/settings").json()
    assert len(s["sources"]) == 3
    assert client.post("/api/worker/settings", json={**s, "scan_interval_hours": -5}).status_code == 422
    assert client.post("/api/worker/settings", json={**s, "scan_interval_hours": 100000}).status_code == 422
    s["scan_interval_hours"] = 8
    s["sources"][0]["enabled"] = False
    r = client.post("/api/worker/settings", json=s)
    assert r.status_code == 200 and r.json()["settings"]["scan_interval_hours"] == 8
    saved = client.get("/api/worker/settings").json()
    assert saved["sources"][0]["enabled"] is False and len(saved["sources"]) == 3


def test_worker_trigger_and_status(monkeypatch):
    from app.services import worker as w

    async def no_ingest(query=""):
        return []

    monkeypatch.setattr(w, "fetch_all_registries", no_ingest)
    r = client.post("/api/worker/trigger")
    assert r.status_code == 200 and r.json()["status"] == "completed"
    st = client.get("/api/worker/status").json()
    assert st["is_running"] is False and st["last_sync"] and st["last_error"] is None
