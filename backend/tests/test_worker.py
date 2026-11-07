import pytest
from fastapi.testclient import TestClient
from main import app
from app.services.registries import (
    clean_search_title,
    parse_company_from_title,
    extract_tech_tags,
    is_listing_page,
    split_query_terms,
)
from app.services.worker import ingestion_worker, load_worker_state

client = TestClient(app)


def test_clean_search_title():
    raw = "Stage Ingénieur Vision par Ordinateur - Welcome to the Jungle"
    cleaned = clean_search_title(raw)
    assert cleaned == "Stage Ingénieur Vision par Ordinateur"


def test_parse_company_from_title():
    comp1 = parse_company_from_title("Stage R&D chez Thales", "https://thalesgroup.com/jobs/123")
    assert "Thales" in comp1

    comp2 = parse_company_from_title("Ingénieur Edge AI at CEA", "https://cea.fr/postes")
    assert "CEA" in comp2


def test_extract_tech_tags_word_boundaries():
    tags = extract_tech_tags("Stage C++ et PyTorch pour déploiement TensorRT sur Jetson Orin")
    assert "C++" in tags
    assert "C" not in tags  # C++ must not falsely trigger C
    assert any(t.lower() == "pytorch" for t in tags)
    assert any(t.lower() == "tensorrt" for t in tags)


def test_is_listing_page_filters_aggregators():
    assert is_listing_page("https://fr.indeed.com/q-stage-ia-emplois.html") is True
    assert is_listing_page("https://fr.indeed.com/viewjob?jk=abc123456") is False


def test_split_query_terms_truncates_safely():
    long_q = "A" * 500 + ", B" * 200
    terms = split_query_terms(long_q, max_terms=3, max_len=80)
    assert len(terms) <= 3
    assert all(len(t) <= 80 for t in terms)


@pytest.mark.asyncio
async def test_worker_sync_cycle_deterministic(monkeypatch):
    async def fake_fetch_all():
        return [
            {
                "id": "job-test-sync-1",
                "title": "Stage Traitement du Signal Radar",
                "company": "Thales",
                "location": "Toulouse",
                "contract": "Stage (6 mois)",
                "category": "Traitement du Signal",
                "tags": ["Python", "Radar", "DSP"],
                "match_score": 88,
                "description": "Stage R&D sur algorithmes radar embarqués.",
                "url": "https://www.thalesgroup.com/fr/career/stage-radar-1",
                "recruiter_type": "Équipe R&D",
                "recruiter_profile": "Cherche profil signal",
                "source": "JobSpy Live (Indeed)",
                "date_posted": "2026-11-01",
                "is_active": True,
            }
        ]

    monkeypatch.setattr("app.services.worker.fetch_all_registries", fake_fetch_all)
    monkeypatch.setattr("app.services.worker.load_worker_settings", lambda: {
        "scan_interval_hours": 6,
        "auto_liveness_check": False,
        "hide_expired_by_default": False,
        "sources": [],
    })

    state = await ingestion_worker.run_sync_cycle()
    assert state is not None
    assert state["total_jobs"] >= 1
    assert state["last_sync"] is not None
    assert state["sources_stats"].get("JobSpy Live (Indeed)") == 1


def test_worker_api_endpoints(monkeypatch):
    # GET status
    res = client.get("/api/worker/status")
    assert res.status_code == 200
    data = res.json()
    assert "total_jobs" in data
    assert "active_jobs" in data

    # GET settings
    res_set = client.get("/api/worker/settings")
    assert res_set.status_code == 200
    settings = res_set.json()
    assert "sources" in settings
    assert len(settings["sources"]) > 0

    # POST valid settings
    settings["scan_interval_hours"] = 8
    res_update = client.post("/api/worker/settings", json=settings)
    assert res_update.status_code == 200
    assert res_update.json()["settings"]["scan_interval_hours"] == 8

    # POST invalid interval rejected (422)
    res_bad = client.post("/api/worker/settings", json={"scan_interval_hours": -5})
    assert res_bad.status_code == 422

    # POST trigger (with stubbed sync cycle)
    async def fast_sync():
        return load_worker_state()

    monkeypatch.setattr(ingestion_worker, "run_sync_cycle", fast_sync)
    res_trig = client.post("/api/worker/trigger")
    assert res_trig.status_code == 200
    assert res_trig.json()["status"] in ("completed", "already_running")
