import pytest
from fastapi.testclient import TestClient
from main import app
from app.services.registries import (
    clean_search_title,
    parse_company_from_title,
    extract_tech_tags,
    load_worker_settings,
    save_worker_settings,
    search_ddgs_live
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

def test_extract_tech_tags():
    tags = extract_tech_tags("Stage C++ et PyTorch pour déploiement TensorRT sur Jetson Orin")
    assert "C++" in tags
    assert "Pytorch" in tags or "PyTorch" in tags
    assert "Tensorrt" in tags or "TensorRT" in tags

def test_ddgs_live_search():
    # Fast targeted query
    results = search_ddgs_live("Traitement du signal", "Toulouse", "welcometothejungle.com", max_results=3)
    assert isinstance(results, list)
    if results:
        assert "title" in results[0]
        assert "url" in results[0]
        assert results[0]["url"].startswith("http")

@pytest.mark.asyncio
async def test_worker_sync_cycle():
    state = await ingestion_worker.run_sync_cycle()
    assert state is not None
    assert "total_jobs" in state
    assert state["last_sync"] is not None
    assert "sources_stats" in state

def test_worker_api_endpoints():
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

    # POST settings
    settings["scan_interval_hours"] = 8
    res_update = client.post("/api/worker/settings", json=settings)
    assert res_update.status_code == 200
    assert res_update.json()["settings"]["scan_interval_hours"] == 8

    # POST trigger
    res_trig = client.post("/api/worker/trigger")
    assert res_trig.status_code == 200
    assert res_trig.json()["status"] in ("completed", "already_running")
