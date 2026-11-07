import pytest
from app.services.agent_reach import agent_reach_service, CURATED_OFFERS
from app.services.cv_parser import parse_cv_to_profile
from app.services.storage import load_profile, save_profile, load_settings, save_settings, load_history, save_history

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

