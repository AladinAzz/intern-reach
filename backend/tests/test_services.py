import pytest
from app.services.agent_reach import agent_reach_service, CURATED_OFFERS
from app.services.cv_parser import parse_cv_to_profile
from app.services.storage import (
    load_profile, save_profile, load_settings, save_settings,
    load_history, save_history, are_jobs_duplicate, upsert_stored_jobs, load_stored_jobs
)

def test_agent_reach_search_all():
    results = agent_reach_service.search_internships("", "Paris, Île-de-France")
    assert len(results) >= 5
    assert any("Thales" in r["company"] for r in results)
    assert any("CEA" in r["company"] for r in results)

def test_agent_reach_search_filtered():
    results = agent_reach_service.search_internships("Radar", "Paris, Île-de-France")
    assert len(results) >= 1
    assert any("Radar" in r["title"] or "Radar" in r["tags"] for r in results)

def test_cv_parser_detection():
    sample_cv = """
    Jean Dupont
    Email: jean.dupont@telecom-paris.fr
    Tel: 06 12 34 56 78
    Formation: Diplôme d'ingénieur spécialité Systèmes Embarqués et IA.
    Compétences: C++, PyTorch, OpenCV, Linux Embarqué, FreeRTOS, ROS 2, FPGA, VHDL, TensorRT.
    Projets:
    - Déploiement d'un modèle YOLOv8 sur NVIDIA Jetson Nano avec quantification INT8.
    - Conception d'un filtre adaptatif sous MATLAB et DSP.
    """
    profile = parse_cv_to_profile(sample_cv)
    assert profile["email"] == "jean.dupont@telecom-paris.fr"
    assert "06 12 34 56 78" in profile["phone"]
    assert "C++" in profile["technical_skills"]
    assert "PyTorch" in profile["technical_skills"]
    assert "ROS 2" in profile["technical_skills"]

def test_storage_operations():
    settings = load_settings()
    assert "active_provider" in settings
    
    profile = load_profile()
    assert "full_name" in profile
    assert len(profile["technical_skills"]) > 0

    history = load_history()
    assert isinstance(history, list)

def test_job_storage_and_deduplication():
    j1 = {
        "id": "test-1",
        "title": "STAGE - Ingénieur.e Linux Embarqué H/F",
        "company": "KNDS France Systems",
        "location": "Toulouse",
        "tags": ["Linux", "C++"],
        "url": "https://fr.indeed.com/viewjob?jk=12345"
    }
    j2 = {
        "id": "test-2",
        "title": "Ingénieur Linux Embarqué (F/H)",
        "company": "KNDS",
        "location": "Toulouse",
        "tags": ["Linux", "C++", "Yocto"],
        "url": "https://fr.indeed.com/viewjob?jk=12345"
    }
    j3 = {
        "id": "test-3",
        "title": "Stage Deep Learning & Vision",
        "company": "Airbus",
        "location": "Toulouse",
        "tags": ["Python", "PyTorch"],
        "url": "https://airbus.com/jobs/999"
    }

    # Verify duplicate detection
    assert are_jobs_duplicate(j1, j2) is True
    assert are_jobs_duplicate(j1, j3) is False

    # Upsert into storage and verify count
    initial_stored = load_stored_jobs()
    initial_len = len(initial_stored)

    # Adding j1 and j2 (duplicates) should only increment unique count by 1
    updated = upsert_stored_jobs([j1, j2])
    assert len(updated) == initial_len + 1 or any(are_jobs_duplicate(j1, ex) for ex in initial_stored)


