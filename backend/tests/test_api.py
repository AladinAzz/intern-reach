import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"

def test_search_endpoint():
    res = client.post("/api/search", json={"query": "Edge AI", "location": "Paris, Île-de-France"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "results" in data
    assert len(data["results"]) > 0

def test_cv_profile_endpoints():
    # GET
    res_get = client.get("/api/cv/profile")
    assert res_get.status_code == 200
    profile = res_get.json()
    assert "full_name" in profile
    assert "technical_skills" in profile

    # POST update
    profile["full_name"] = "Dr. Test Engineer"
    res_post = client.post("/api/cv/profile", json=profile)
    assert res_post.status_code == 200
    updated = res_post.json()["profile"]
    assert updated["full_name"] == "Dr. Test Engineer"

def test_settings_endpoint():
    res_get = client.get("/api/settings")
    assert res_get.status_code == 200
    settings = res_get.json()
    assert settings["active_provider"] == "gemini"
    assert "gemini_api_key" in settings
    # Key should be masked
    if settings["gemini_api_key"]:
        assert "..." in settings["gemini_api_key"]

def test_ssrf_blocked_on_import():
    # Attempting to import from localhost / private loopback
    res = client.post("/api/search/import-offer", json={"url": "http://127.0.0.1:8000/api/settings"})
    assert res.status_code == 200
    offer = res.json()["offer"]
    # Should not fetch internal endpoints
    assert "privé" in offer["description"] or "bloquée" in offer["description"]

def test_upload_file_size_limit():
    # Construct simulated oversized file (>10MB)
    oversized = b"0" * (10 * 1024 * 1024 + 100)
    files = {"file": ("big_cv.txt", oversized, "text/plain")}
    res = client.post("/api/cv/upload", files=files)
    assert res.status_code == 413
    assert "volumineux" in res.json()["detail"]

def test_history_endpoint():
    entry_id = "test-history-unique-run"
    entry = {
        "id": entry_id,
        "job_title": "Stage Test",
        "company": "Test Aerospace",
        "location": "Paris",
        "url": "https://example.com",
        "applied_at": "07/11/2026",
        "status": "Enregistré",
        "selected_version": "R&D / Scientifique",
        "letter_content": "Lettre de motivation de test."
    }
    # Create or update
    res = client.post("/api/history", json=entry)
    assert res.status_code == 200
    history = client.get("/api/history").json()
    assert any(h["id"] == entry_id for h in history)

    # Patch status
    res_patch = client.patch(f"/api/history/{entry_id}/status", json={"status": "Entretien"})
    assert res_patch.status_code == 200
    patched_history = res_patch.json()["history"]
    assert any(h["id"] == entry_id and h["status"] == "Entretien" for h in patched_history)

    # Clean up entry so tests leave clean state
    res_del = client.delete(f"/api/history/{entry_id}")
    assert res_del.status_code == 200
    final_history = res_del.json()["history"]
    assert not any(h["id"] == entry_id for h in final_history)

def test_letter_generation_endpoint():
    job_mock = {
        "id": "mock-thales",
        "title": "Stage Traitement du Signal",
        "company": "Thales",
        "location": "Gennevilliers",
        "contract": "Stage",
        "category": "Traitement du Signal",
        "tags": ["MATLAB", "C++", "DSP"],
        "match_score": 95,
        "description": "Développement d'algorithmes de filtrage adaptatif.",
        "url": "https://example.com",
        "recruiter_type": "Défense",
        "recruiter_profile": "Rigueur et validation numérique."
    }
    res = client.post("/api/letters/generate", json={"job": job_mock})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["versions"]) == 3
    # Check that the 3 versions are distinct
    labels = [v["label"] for v in data["versions"]]
    assert "R&D / Scientifique" in labels
    assert "Tech Agile / Startup" in labels
    assert "Grand Groupe Industriel" in labels

def test_import_offer_endpoint():
    raw_text = """
    Stage - Vision par Ordinateur et Edge AI
    Entreprise: Safran Electronics
    Lieu: Massy
    Missions: Deploiement de transformeurs visuels sur cibles NVIDIA Jetson Orin.
    Competences: Python, PyTorch, C++, TensorRT, OpenCV.
    """
    res = client.post("/api/search/import-offer", json={"raw_text": raw_text})
    assert res.status_code == 200
    offer = res.json()["offer"]
    assert "title" in offer
    assert "company" in offer
    assert "tags" in offer
    assert len(offer["tags"]) > 0

def test_pitch_and_gap_endpoint():
    job_mock = {
        "id": "mock-thales",
        "title": "Stage Traitement du Signal",
        "company": "Thales",
        "category": "Traitement du Signal",
        "tags": ["C++", "PyTorch", "MATLAB", "FPGA"]
    }
    res = client.post("/api/letters/pitch-and-gap", json={"job": job_mock})
    assert res.status_code == 200
    analysis = res.json()["analysis"]
    assert "cold_email_subject" in analysis
    assert "cold_email_body" in analysis
    assert "linkedin_note" in analysis
    assert "bridge_advice" in analysis
    assert "matched_skills" in analysis
    assert "missing_skills" in analysis

def test_interview_prep_endpoint():
    job_mock = {
        "id": "mock-thales",
        "title": "Stage Traitement du Signal",
        "company": "Thales",
        "category": "Traitement du Signal",
        "description": "Filtrage numerique et radar.",
        "tags": ["C++", "PyTorch", "MATLAB"]
    }
    res = client.post("/api/letters/interview-prep", json={"job": job_mock})
    assert res.status_code == 200
    questions = res.json()["questions"]
    assert len(questions) == 5
    assert "question" in questions[0]
    assert "expected_answer" in questions[0]
    assert "tip" in questions[0]

def test_suggest_keywords_endpoint():
    profile_sample = {
        "full_name": "Ingénieur Test",
        "education": "Master 2 E3A Université Paris-Saclay",
        "target_domains": ["Systèmes Embarqués", "Linux RT", "Edge AI"],
        "technical_skills": ["C++", "FreeRTOS", "STM32", "ROS 2"],
        "key_projects": [{"title": "CubeSat", "desc": "Bus I2C et télémétrie"}]
    }
    res = client.post("/api/search/suggest-keywords", json={"profile": profile_sample})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "suggested_query" in data
    assert len(data["suggested_query"]) > 0
    assert "specialties" in data
    assert len(data["specialties"]) > 0
    assert "alternative_queries" in data
    assert len(data["alternative_queries"]) >= 1
    assert "rationale" in data


