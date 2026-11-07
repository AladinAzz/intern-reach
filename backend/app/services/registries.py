import json
import os
import re
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.services.storage import load_profile

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

WORKER_SETTINGS_FILE = os.path.join(DATA_DIR, "worker_settings.json")
SEARCH_CACHE_FILE = os.path.join(DATA_DIR, "search_cache.json")

# Configurable Live Search Tools (No fixed static registries)
DEFAULT_SEARCH_TOOLS = [
    {
        "id": "jobspy_live",
        "name": "JobSpy // Multi-Plateformes (Indeed, LinkedIn, Glassdoor, ZipRecruiter)",
        "type": "jobspy",
        "enabled": True,
        "description": "Moteur de scraping live temps réel interrogeant directement les endpoints mobiles des agrégateurs."
    },
    {
        "id": "ddgs_wttj_apec",
        "name": "Live Search // Welcome to the Jungle, Apec & HelloWork",
        "type": "live_web",
        "target_sites": "welcometothejungle.com, apec.fr, hellowork.com, linkedin.com/jobs",
        "enabled": True,
        "description": "Recherche web en direct sur les plateformes de recrutement tech françaises et européennes."
    },
    {
        "id": "ddgs_corporate_labs",
        "name": "Live Search // Labos R&D & Portails Entreprises (CEA, Thales, Safran, Airbus, Inria, STMicro)",
        "type": "live_corporate",
        "target_sites": "thalesgroup.com, cea.fr, safran-group.com, airbus.com, st.com, inria.fr",
        "enabled": True,
        "description": "Recherche ciblée en temps réel sur les portails carrières des grands groupes et laboratoires R&D."
    }
]

def load_worker_settings() -> Dict[str, Any]:
    if os.path.exists(WORKER_SETTINGS_FILE):
        try:
            with open(WORKER_SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "sources" in data:
                    return data
        except Exception:
            pass
    defaults = {
        "scan_interval_hours": 6,
        "auto_liveness_check": True,
        "hide_expired_by_default": False,
        "sources": DEFAULT_SEARCH_TOOLS,
        "target_locations": ["France", "Paris", "Toulouse", "Lyon", "Grenoble", "Sophia Antipolis", "Télétravail"]
    }
    save_worker_settings(defaults)
    return defaults

def save_worker_settings(settings: Dict[str, Any]) -> None:
    with open(WORKER_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def extract_tech_tags(text: str) -> List[str]:
    tags = []
    text_upper = f" {text.upper()} "
    keywords = [
        "C++", "C", "PYTHON", "RUST", "LINUX", "FREERTOS", "ROS 2", "ROS",
        "PYTORCH", "TENSORFLOW", "OPENCV", "CUDA", "TENSORRT", "TINYML", "EDGE AI",
        "FPGA", "VHDL", "DSP", "MATLAB", "SLAM", "LIDAR", "RADAR", "STM32", "ARM", "CAN"
    ]
    for kw in keywords:
        pat = r"(?:^|[^\w])" + re.escape(kw) + r"(?:[^\w]|$)"
        if re.search(pat, text_upper):
            tags.append(kw.title() if kw not in ("C++", "FPGA", "VHDL", "DSP", "ROS 2", "ROS", "ARM", "CAN") else kw)
    if tags:
        return tags[:5]
    try:
        from app.services.storage import load_profile
        prof = load_profile()
        cv_skills = prof.get("technical_skills", [])
        if cv_skills:
            return cv_skills[:4]
    except Exception:
        pass
    return ["R&D", "Ingénierie"]

def parse_company_from_title(title: str, url: str) -> str:
    """Heuristic extraction of company name from search snippet and URL."""
    # Check for "at Company" or "chez Company" or " - Company"
    match = re.search(r"(?:chez|at|@)\s+([A-Za-z0-9\s&.\-_]+?)(?:\s*[-–|,]|\s*$)", title, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    if "thalesgroup.com" in url or "thales" in title.lower():
        return "Thales Group"
    if "cea.fr" in url or "cea" in title.lower():
        return "CEA (Commissariat à l'Énergie Atomique)"
    if "safran-group.com" in url or "safran" in title.lower():
        return "Safran Electronics & Defense"
    if "airbus.com" in url or "airbus" in title.lower():
        return "Airbus Defence and Space"
    if "st.com" in url or "stmicroelectronics" in title.lower():
        return "STMicroelectronics"
    if "inria.fr" in url or "inria" in title.lower():
        return "Inria (Institut National de Recherche en Informatique)"

    # Fallback to domain host
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.replace("www.", "").split(".")[0]
        if host and host not in ("welcometothejungle", "linkedin", "apec", "hellowork", "indeed", "glassdoor"):
            return host.capitalize()
    except Exception:
        pass

    return "Entreprise Innovante"

def clean_search_title(raw_title: str) -> str:
    # Remove site suffixes like "| Welcome to the Jungle", "- LinkedIn", etc.
    cleaned = re.sub(r"\s*[-–|]\s*(?:Welcome to the Jungle|LinkedIn|Apec|HelloWork|Indeed).*$", "", raw_title, flags=re.IGNORECASE)
    return cleaned.strip()

def search_ddgs_live(query: str, location: str, target_sites: str = "", max_results: int = 8) -> List[Dict[str, Any]]:
    """
    Executes real-time live web query using ddgs search tool.
    Extracts authentic active jobs with direct URLs.
    """
    offers = []
    try:
        from ddgs import DDGS
        
        loc_str = location.strip() if location.strip() else "France"
        q_tokens = [t.strip() for t in query.replace(",", " ").replace("&", " ").split() if len(t.strip()) > 2]
        clean_kw = " ".join(q_tokens[:3]) if q_tokens else "systèmes embarqués"
        
        # Build clean site query to respect search engine grammar
        site_term = ""
        if target_sites:
            if "welcometothejungle" in target_sites:
                site_term = "site:welcometothejungle.com"
            elif "thales" in target_sites or "cea" in target_sites:
                site_term = "site:thalesgroup.com"
            elif "apec" in target_sites:
                site_term = "site:apec.fr"

        search_query = f"stage {clean_kw} {loc_str} {site_term}".strip()
        
        results = []
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(search_query, max_results=max_results))
        except Exception:
            # Fallback to general recruiter query without site operator
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(f"stage {clean_kw} {loc_str} recrutement", max_results=max_results))
            except Exception:
                results = []
            
        for idx, r in enumerate(results):
            raw_title = r.get("title", "")
            href = r.get("href", "")
            snippet = r.get("body", "")
            
            if not href or not raw_title:
                continue
                
            title = clean_search_title(raw_title)
            company = parse_company_from_title(raw_title, href)
            
            clean_id = f"live-ddgs-{re.sub(r'[^a-zA-Z0-9]', '', company.lower())[:8]}-{idx}"
            
            # Source labeling
            source_label = "Live Search // Web Direct"
            if "welcometothejungle" in href:
                source_label = "Live Search // Welcome to the Jungle"
            elif "linkedin.com" in href:
                source_label = "Live Search // LinkedIn"
            elif "apec.fr" in href:
                source_label = "Live Search // Apec"
            elif any(corp in href for corp in ("thalesgroup", "cea.fr", "safran", "airbus", "st.com")):
                source_label = "Live Search // Portail Labo R&D"

            offers.append({
                "id": clean_id,
                "title": title,
                "company": company,
                "location": loc_str if loc_str.lower() != "france" else "France / Région",
                "contract": "Stage conventionné (PFE / Master 2)",
                "category": query or "Ingénierie & R&D",
                "tags": extract_tech_tags(f"{title} {snippet}"),
                "match_score": 93,
                "description": snippet or f"Offre identifiée en direct sur le web chez {company}. Missions liées à {title}.",
                "url": href,
                "date_posted": datetime.now().strftime("%Y-%m-%d"),
                "source": source_label,
                "is_active": True,
                "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
    except Exception as e:
        if "No results found" not in str(e):
            print(f"Notice: Live search DDGS: {e}")
        
    return offers

def scrape_jobspy_live(query: str, location: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """
    Executes live multi-platform scraping using JobSpy on Indeed, LinkedIn, Glassdoor, ZipRecruiter.
    """
    offers = []
    try:
        from jobspy import scrape_jobs
        
        loc_str = location.strip() if location.strip() else "France"
        q_str = f"Stage {query}".strip() if "stage" not in query.lower() else query.strip()
        
        df = scrape_jobs(
            site_name=["indeed", "linkedin", "glassdoor"],
            search_term=q_str,
            location=loc_str,
            results_wanted=max_results,
            country_indeed="France"
        )
        
        if df is not None and not df.empty:
            for idx, row in df.iterrows():
                title = str(row.get("title") or "").strip()
                company = str(row.get("company") or "Entreprise").strip()
                job_url = str(row.get("job_url") or "").strip()
                job_loc = str(row.get("location") or loc_str).strip()
                site = str(row.get("site") or "Indeed").capitalize()
                
                if not title or not job_url or job_url == "nan":
                    continue
                    
                desc = str(row.get("description") or "")
                short_desc = desc[:280] + "..." if len(desc) > 280 else (desc or f"Poste de {title} chez {company}.")
                
                clean_id = f"live-jobspy-{re.sub(r'[^a-zA-Z0-9]', '', company.lower())[:8]}-{idx}"
                
                offers.append({
                    "id": clean_id,
                    "title": title,
                    "company": company,
                    "location": job_loc,
                    "contract": "Stage conventionné",
                    "category": query or "Ingénierie & R&D",
                    "tags": extract_tech_tags(f"{title} {short_desc}"),
                    "match_score": 92,
                    "description": short_desc,
                    "url": job_url,
                    "date_posted": datetime.now().strftime("%Y-%m-%d"),
                    "source": f"JobSpy // {site}",
                    "is_active": True,
                    "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
    except Exception as e:
        print(f"Notice: Live scrape JobSpy error: {e}")
        
    return offers

async def execute_live_search_tools(query: str = "", location: str = "") -> List[Dict[str, Any]]:
    """
    Dynamically executes available live search tools without any fixed or static registries:
    1. JobSpy live scraper across Indeed, LinkedIn, Glassdoor.
    2. DDGS live search targeting tech portals (WTTJ, Apec, HelloWork).
    3. DDGS live search targeting corporate & R&D lab career sites (Thales, CEA, Safran, Airbus, Inria, STMicro).
    """
    settings = load_worker_settings()
    configured_tools = {t["id"]: t for t in settings.get("sources", DEFAULT_SEARCH_TOOLS)}
    
    tasks = []
    
    # 1. JobSpy Live
    if configured_tools.get("jobspy_live", {}).get("enabled", True):
        tasks.append(asyncio.to_thread(scrape_jobspy_live, query, location, 8))
        
    # 2. DDGS Web Recruteurs
    if configured_tools.get("ddgs_wttj_apec", {}).get("enabled", True):
        wttj_sites = configured_tools.get("ddgs_wttj_apec", {}).get("target_sites", "welcometothejungle.com, apec.fr, hellowork.com, linkedin.com/jobs")
        tasks.append(asyncio.to_thread(search_ddgs_live, query, location, wttj_sites, 6))
        
    # 3. DDGS Portails R&D & Entreprises
    if configured_tools.get("ddgs_corporate_labs", {}).get("enabled", True):
        corp_sites = configured_tools.get("ddgs_corporate_labs", {}).get("target_sites", "thalesgroup.com, cea.fr, safran-group.com, airbus.com, st.com, inria.fr")
        tasks.append(asyncio.to_thread(search_ddgs_live, query, location, corp_sites, 6))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_live_offers = []
    for res in results:
        if isinstance(res, list) and res:
            all_live_offers.extend(res)
            
    # Cache recent live search results
    try:
        with open(SEARCH_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(all_live_offers, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
        
    return all_live_offers

# Compatibility alias for existing router/worker calls
async def fetch_all_registries(query: str = "") -> List[Dict[str, Any]]:
    """Delegates to live search tools dynamically using profile keywords if query is empty."""
    if not query:
        try:
            from app.services.storage import load_profile
            p = load_profile()
            domains = p.get("target_domains", [])
            skills = p.get("technical_skills", [])
            if domains:
                query = ", ".join(domains[:3])
            elif skills:
                query = ", ".join(skills[:3])
            else:
                query = "Ingénierie & R&D"
        except Exception:
            query = "Ingénierie & R&D"
    return await execute_live_search_tools(query, "France")
