import io
import re
import json
from typing import Dict, Any, List
from pypdf import PdfReader
from app.services.storage import save_profile, load_profile

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text.strip()
    except Exception as e:
        return f"Erreur lors de l'extraction PDF: {str(e)}"

def parse_cv_to_profile(text: str) -> Dict[str, Any]:
    """
    Synchronous fallback regex extraction.
    """
    profile = load_profile()
    profile["raw_cv_text"] = text

    # Extract email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if email_match:
        profile["email"] = email_match.group(0)

    # Extract phone
    phone_match = re.search(r"(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}", text)
    if phone_match:
        profile["phone"] = phone_match.group(0)

    # Extract Name heuristic from first lines if present
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:10]:
        # If line looks like a name (2-3 words, no symbols, not starting with contact/skills)
        if re.match(r"^[A-Z][a-zÀ-ÿ]+(?:\s+[A-ZÀ-ÿ]+){1,3}$", line):
            if not any(k in line.lower() for k in ("contact", "skills", "languages", "profil", "curriculum")):
                profile["full_name"] = line
                break

    # Keywords detection for technical skills
    common_skills = [
        "C++", "C++17", "C++20", "C", "Python", "PyTorch", "TensorFlow", "MATLAB", "Simulink",
        "OpenCV", "CUDA", "TensorRT", "Linux", "Linux Embarqué", "Yocto", "FreeRTOS", "RTOS",
        "ROS", "ROS 2", "VHDL", "Verilog", "FPGA", "Vivado", "Xilinx", "ARM", "STM32",
        "CAN", "SPI", "I2C", "UART", "TinyML", "Edge AI", "Computer Vision",
        "Traitement du signal", "Traitement d'images", "Kalman", "SLAM", "Docker", "Git"
    ]
    detected_skills = []
    text_upper = text.upper()
    for s in common_skills:
        s_upper = s.upper()
        pattern = r"(?:^|[^\w])" + re.escape(s_upper) + r"(?:[^\w]|$)"
        if re.search(pattern, text_upper):
            if s not in detected_skills:
                detected_skills.append(s)
    
    if detected_skills:
        profile["technical_skills"] = detected_skills

    save_profile(profile)
    return profile

async def parse_cv_with_ai(text: str) -> Dict[str, Any]:
    """
    Intelligent CV parsing using LLM with graceful fallback to regex parser.
    """
    # 1. Base parsing with regex
    profile = parse_cv_to_profile(text)

    # 2. Augment with AI if possible
    try:
        from app.services.letter_generator import letter_generator
        prompt = f"""
Tu es un parseur d'extraction de CV expert pour les profils ingénieurs / scientifiques.
Extrais les informations de ce CV sous format JSON STRICT sans aucun texte superflu :
{{
  "full_name": "Prénom et Nom complet du candidat",
  "email": "Email",
  "phone": "Numéro de téléphone au format lisible",
  "education": "Intitulé précis de la formation actuelle ou diplôme principal (ex: Master 1 E3A / Université Paris-Saclay)",
  "target_domains": ["Domaine cible 1", "Domaine cible 2", "Domaine cible 3"],
  "technical_skills": ["Compétence 1", "Compétence 2", "Compétence 3"],
  "key_projects": [
    {{"title": "Titre du projet / stage", "desc": "Description synthétique et concrète des réalisations"}}
  ]
}}

Texte brut du CV :
\"\"\"
{text[:3500]}
\"\"\"
"""
        ai_resp = await letter_generator.call_llm(prompt)
        if ai_resp:
            clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", ai_resp.strip(), flags=re.MULTILINE)
            extracted = json.loads(clean_json)

            if extracted.get("full_name"):
                profile["full_name"] = extracted["full_name"]
            if extracted.get("email"):
                profile["email"] = extracted["email"]
            if extracted.get("phone"):
                profile["phone"] = extracted["phone"]
            if extracted.get("education"):
                profile["education"] = extracted["education"]
            if extracted.get("target_domains") and isinstance(extracted["target_domains"], list):
                profile["target_domains"] = extracted["target_domains"]
            if extracted.get("technical_skills") and isinstance(extracted["technical_skills"], list) and len(extracted["technical_skills"]) > 0:
                profile["technical_skills"] = extracted["technical_skills"]
            if extracted.get("key_projects") and isinstance(extracted["key_projects"], list) and len(extracted["key_projects"]) > 0:
                profile["key_projects"] = extracted["key_projects"]

            save_profile(profile)
    except Exception as e:
        print(f"Notice: AI CV parsing fallback to regex: {e}")

    return profile
