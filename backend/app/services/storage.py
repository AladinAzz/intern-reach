import json
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

PROFILE_FILE = os.path.join(DATA_DIR, "profile.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

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
                return json.load(f)
        except Exception:
            pass
    return []

def save_history(history: List[Dict[str, Any]]) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def add_history_entry(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    history = load_history()
    # Prepend newest
    history.insert(0, entry)
    save_history(history)
    return history

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

