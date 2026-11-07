import io
import re
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
        # For skills with symbols like C++ or C#, match with non-word or start/end boundary instead of \b
        pattern = r"(?:^|[^\w])" + re.escape(s_upper) + r"(?:[^\w]|$)"
        if re.search(pattern, text_upper):
            if s not in detected_skills:
                detected_skills.append(s)
    
    if detected_skills:
        # Merge with existing skills without duplicates
        existing = set(profile.get("technical_skills", []))
        for s in detected_skills:
            existing.add(s)
        profile["technical_skills"] = list(existing)

    save_profile(profile)
    return profile

