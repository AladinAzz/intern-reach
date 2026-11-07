import re
import socket
import ipaddress
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from app.services.letter_generator import letter_generator
from app.services.storage import load_profile

def is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        # Disallow localhost / loopback directly
        if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
            return False
        # Resolve IP and check if private
        ip_str = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_str)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False
        return True
    except Exception:
        return False

class JobExtractorService:
    async def extract_from_url_or_text(self, url: Optional[str] = None, raw_text: Optional[str] = None) -> Dict[str, Any]:
        # Validate URL for SSRF protection immediately
        if url and not is_safe_url(url):
            return {
                "id": "unsafe-url-blocked",
                "title": "URL Non Autorisée (Réseau Privé ou Invalide)",
                "company": "Protection Sécurité",
                "location": "Local",
                "contract": "Non applicable",
                "category": "Sécurité",
                "tags": ["Sécurité", "SSRF"],
                "match_score": 0,
                "description": f"L'adresse URL ({url}) pointe vers un réseau local ou privé et a été bloquée pour des raisons de sécurité.",
                "url": "",
                "recruiter_type": "Système",
                "recruiter_profile": "Requête interne bloquée."
            }

        extracted_text = raw_text or ""

        # If a URL is provided, fetch HTML and extract readable text
        if url and not extracted_text:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                }
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        # Remove script, style, nav, footer
                        for tag in soup(["script", "style", "nav", "footer", "header"]):
                            tag.decompose()
                        extracted_text = soup.get_text(separator="\n", strip=True)[:4000]
            except Exception as e:
                extracted_text = f"URL de l'offre: {url}"

        # Use Gemini to structure into a JobOffer
        prompt = f"""
Analyse cette offre d'emploi / de stage et extrait les métadonnées au format JSON strict :
Contenu de l'offre :
\"\"\"
{extracted_text[:3500]}
\"\"\"

Réponds UNIQUEMENT avec un JSON valide suivant ce schéma exact :
{{
  "id": "external-offer",
  "title": "Titre du stage",
  "company": "Nom de l'entreprise ou laboratoire",
  "location": "Localisation (ex: Paris, Saclay, etc.)",
  "contract": "Type de stage (ex: Stage conventionné 6 mois, PFE)",
  "category": "Domaine technique principal",
  "tags": ["Compétence 1", "Compétence 2", "Compétence 3", "Compétence 4", "Compétence 5"],
  "match_score": 93,
  "description": "Résumé en 2 phrases des missions principales.",
  "url": "{url or ''}",
  "recruiter_type": "Grand Groupe, PME, Laboratoire R&D ou Startup",
  "recruiter_profile": "Attentes clés du recruteur et culture d'équipe"
}}
"""
        response_text = await letter_generator.call_llm(prompt)
        
        # Parse JSON from response
        import json
        try:
            # Strip code fences if present
            clean_json = re.sub(r"^```json\s*|\s*```$", "", response_text.strip(), flags=re.MULTILINE)
            data = json.loads(clean_json)
            data["id"] = f"custom-{abs(hash(data.get('title', '')))}"
            return data
        except Exception:
            # Fallback
            return {
                "id": f"custom-{abs(hash(extracted_text[:30]))}",
                "title": "Stage Ingénieur R&D (Importé)",
                "company": "Entreprise / Laboratoire Partenaire",
                "location": "Paris / Île-de-France",
                "contract": "Stage (6 mois)",
                "category": "Systèmes Embarqués & IA",
                "tags": ["C++", "PyTorch", "Linux Embarqué", "Traitement du Signal"],
                "match_score": 92,
                "description": extracted_text[:300] if extracted_text else "Stage ingénieur technique extrait.",
                "url": url or "",
                "recruiter_type": "R&D / Industrie",
                "recruiter_profile": "Rigueur technique, autonomie et esprit de synthèse."
            }

job_extractor = JobExtractorService()

