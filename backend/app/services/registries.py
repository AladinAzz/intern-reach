import asyncio
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from app.services.storage import (
    DATA_DIR,
    STORE_LOCK,
    atomic_write_json,
    read_json,
    load_profile,
    is_blank,
)

WORKER_SETTINGS_FILE = os.path.join(DATA_DIR, "worker_settings.json")
SEARCH_CACHE_FILE = os.path.join(DATA_DIR, "search_cache.json")

# Hard ceiling per live tool: a blocked scraper must never hang a request or the worker.
TOOL_TIMEOUT_SECONDS = 60

# Configurable live search tools (no fixed/static job registries: every offer comes from a live query).
DEFAULT_SEARCH_TOOLS = [
    {
        "id": "jobspy_live",
        "name": "JobSpy // Multi-Plateformes (Indeed, LinkedIn, Glassdoor)",
        "type": "jobspy",
        "enabled": True,
        "description": "Moteur de scraping live interrogeant directement les agrégateurs d'offres.",
    },
    {
        "id": "ddgs_wttj_apec",
        "name": "Live Search // Welcome to the Jungle, Apec & HelloWork",
        "type": "live_web",
        "target_sites": "welcometothejungle.com, apec.fr, hellowork.com",
        "enabled": True,
        "description": "Recherche web en direct sur les plateformes de recrutement françaises.",
    },
    {
        "id": "ddgs_corporate_labs",
        "name": "Live Search // Portails carrières (grands groupes & laboratoires)",
        "type": "live_corporate",
        "target_sites": "thalesgroup.com, cea.fr, safran-group.com, airbus.com, st.com, inria.fr",
        "enabled": True,
        "description": "Recherche ciblée en temps réel sur les portails carrières des grands groupes et laboratoires R&D.",
    },
]


def _default_worker_settings() -> Dict[str, Any]:
    return {
        "scan_interval_hours": 6,
        "auto_liveness_check": True,
        "hide_expired_by_default": False,
        "sources": [dict(t) for t in DEFAULT_SEARCH_TOOLS],
        "target_locations": ["France", "Paris", "Toulouse", "Lyon", "Grenoble", "Sophia Antipolis", "Télétravail"],
    }


def normalize_worker_settings(data: Any) -> Dict[str, Any]:
    """Merge user-provided settings onto the defaults. Only the ``enabled`` flag of known sources is user-editable."""
    settings = _default_worker_settings()
    if not isinstance(data, dict):
        return settings
    try:
        interval = int(data.get("scan_interval_hours", settings["scan_interval_hours"]))
        settings["scan_interval_hours"] = max(1, min(168, interval))
    except (TypeError, ValueError):
        pass
    for key in ("auto_liveness_check", "hide_expired_by_default"):
        if isinstance(data.get(key), bool):
            settings[key] = data[key]
    locs = data.get("target_locations")
    if isinstance(locs, list):
        clean = [str(l).strip() for l in locs if str(l).strip()][:30]
        if clean:
            settings["target_locations"] = clean
    incoming = data.get("sources")
    if isinstance(incoming, list):
        flags = {s.get("id"): s.get("enabled") for s in incoming if isinstance(s, dict) and isinstance(s.get("enabled"), bool)}
        for src in settings["sources"]:
            if src["id"] in flags:
                src["enabled"] = flags[src["id"]]
    return settings


def load_worker_settings() -> Dict[str, Any]:
    return normalize_worker_settings(read_json(WORKER_SETTINGS_FILE, {}))


def save_worker_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    clean = normalize_worker_settings(settings)
    with STORE_LOCK:
        atomic_write_json(WORKER_SETTINGS_FILE, clean)
    return clean


# ---------------------------------------------------------------------------
# Tag extraction (shared by every search tool)
# ---------------------------------------------------------------------------

# Canonical spellings for well-known technical terms. Profile skills are matched dynamically on top of this.
TECH_TERMS = [
    "C++", "C", "Python", "Rust", "Java", "JavaScript", "TypeScript", "SQL", "Linux", "FreeRTOS", "RTOS", "ROS 2", "ROS",
    "PyTorch", "TensorFlow", "OpenCV", "CUDA", "TensorRT", "TinyML", "Edge AI", "Machine Learning", "Deep Learning",
    "FPGA", "VHDL", "Verilog", "DSP", "MATLAB", "Simulink", "SLAM", "LiDAR", "Radar", "STM32", "ARM",
    "CAN", "I2C", "SPI", "UART", "Docker", "Git", "YOLO", "Excel", "Power BI", "AutoCAD", "SolidWorks",
]


def _contains_term(haystack_upper: str, term: str) -> bool:
    pat = r"(?<![\w+#])" + re.escape(term.upper()) + r"(?![\w+#])"
    return re.search(pat, haystack_upper) is not None


def extract_tech_tags(text: str, profile: Optional[Dict[str, Any]] = None, limit: int = 6) -> List[str]:
    """Tags found in ``text``: well-known technical terms plus the candidate's own CV skills. Empty if none."""
    text_upper = f" {str(text or '').upper()} "
    tags: List[str] = []
    for term in TECH_TERMS:
        if _contains_term(text_upper, term) and term not in tags:
            tags.append(term)
    try:
        prof = profile if profile is not None else load_profile()
        for skill in prof.get("technical_skills", []):
            skill = str(skill).strip()
            if 2 <= len(skill) <= 40 and _contains_term(text_upper, skill) and not any(skill.lower() == t.lower() for t in tags):
                tags.append(skill)
    except Exception:
        pass
    return tags[:limit]


# ---------------------------------------------------------------------------
# DDGS live web search
# ---------------------------------------------------------------------------

_KNOWN_COMPANIES = (
    ("thalesgroup.com", "thales", "Thales Group"),
    ("cea.fr", "cea", "CEA (Commissariat à l'Énergie Atomique)"),
    ("safran-group.com", "safran", "Safran"),
    ("airbus.com", "airbus", "Airbus"),
    ("st.com", "stmicroelectronics", "STMicroelectronics"),
    ("inria.fr", "inria", "Inria"),
)
_AGGREGATOR_HOSTS = ("welcometothejungle", "linkedin", "apec", "hellowork", "indeed", "glassdoor", "jooble", "talent", "adzuna", "monster", "google")
# Result URLs that are search/listing pages rather than a single job posting.
_LISTING_URL = re.compile(
    r"(?:/q-[^/?]*-emplois[^/?]*(?:\.html)?(?:\?.*)?$|/(?:emplois?|jobs?|stages?|search|recherche)/?(?:\?.*)?$|jooble\.org)",
    re.IGNORECASE,
)


def is_listing_page(url: str) -> bool:
    return bool(_LISTING_URL.search(url or ""))


def parse_company_from_title(title: str, url: str) -> str:
    """Heuristic extraction of the company name from a search snippet title and URL."""
    match = re.search(r"(?:\bchez|\bat\b|@)\s+([A-Za-z0-9\s&.\-_]+?)(?:\s*[-–|,]|\s*$)", title, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    url_l = (url or "").lower()
    title_l = (title or "").lower()
    for domain, keyword, display in _KNOWN_COMPANIES:
        if domain in url_l or re.search(rf"\b{re.escape(keyword)}\b", title_l):
            return display

    try:
        host = urlparse(url).netloc.lower().replace("www.", "").split(".")[0]
        if host and not any(a in host for a in _AGGREGATOR_HOSTS):
            return host.capitalize()
    except Exception:
        pass
    return "Entreprise non précisée"


def clean_search_title(raw_title: str) -> str:
    cleaned = re.sub(r"\s*[-–|]\s*(?:Welcome to the Jungle|LinkedIn|Apec|HelloWork|Indeed).*$", "", raw_title, flags=re.IGNORECASE)
    return cleaned.strip()


def split_query_terms(query: str, max_terms: int = 2, max_len: int = 80) -> List[str]:
    """Comma/ampersand separated keyword string -> a few clean search terms."""
    parts = [p.strip() for p in re.split(r"[,;/|]|\s&\s", query or "") if p.strip()]
    seen, out = set(), []
    for p in parts:
        p = p[:max_len]
        if p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return out[:max_terms]


def _site_list(target_sites: str, limit: int = 3) -> List[str]:
    return [s.strip() for s in (target_sites or "").split(",") if s.strip()][:limit]


def search_ddgs_live(query: str, location: str, target_sites: str = "", max_results: int = 8) -> List[Dict[str, Any]]:
    """Real-time web query through ddgs; returns direct posting URLs only (listing pages are filtered out)."""
    offers: List[Dict[str, Any]] = []
    try:
        from ddgs import DDGS
    except Exception as e:
        print(f"Notice: ddgs unavailable: {e}")
        return offers

    loc_str = location.strip() or "France"
    terms = split_query_terms(query, max_terms=1) or [""]
    keyword = " ".join(terms[0].split()[:5])

    sites = _site_list(target_sites)
    queries: List[str] = []
    if sites:
        per_site = max(2, max_results // len(sites))
        queries = [(f"stage {keyword} {loc_str} site:{s}".strip(), per_site) for s in sites]
    else:
        queries = [(f"stage {keyword} {loc_str} recrutement".strip(), max_results)]

    seen_urls = set()
    for search_query, limit in queries:
        results: List[Dict[str, Any]] = []
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(search_query, max_results=limit))
        except Exception as e:
            if "No results found" not in str(e):
                print(f"Notice: Live search DDGS: {e}")
            continue

        for r in results:
            raw_title = r.get("title", "") or ""
            href = (r.get("href", "") or "").strip()
            snippet = r.get("body", "") or ""
            if not href or not raw_title or not href.startswith(("http://", "https://")):
                continue
            if href in seen_urls or is_listing_page(href):
                continue
            seen_urls.add(href)

            title = clean_search_title(raw_title)
            company = parse_company_from_title(raw_title, href)

            host = urlparse(href).netloc.lower()
            if "welcometothejungle" in host:
                source_label = "Live Search // Welcome to the Jungle"
            elif "linkedin.com" in host:
                source_label = "Live Search // LinkedIn"
            elif "apec.fr" in host:
                source_label = "Live Search // Apec"
            elif "hellowork" in host:
                source_label = "Live Search // HelloWork"
            elif any(domain in host for domain, _, _ in _KNOWN_COMPANIES):
                source_label = "Live Search // Portail Carrières"
            else:
                source_label = "Live Search // Web Direct"

            offers.append({
                "title": title,
                "company": company,
                "location": loc_str,
                "contract": "Stage",
                "category": query or "Stage",
                "tags": extract_tech_tags(f"{title} {snippet}"),
                "description": snippet,
                "url": href,
                # No reliable publication date from a web search snippet: storage marks it as "first seen".
                "date_posted": "",
                "source": source_label,
                "is_active": True,
                "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
    return offers


# ---------------------------------------------------------------------------
# JobSpy live scraping
# ---------------------------------------------------------------------------

def _clean_cell(val: Any, default: str = "") -> str:
    if val is None:
        return default
    try:
        import pandas as pd
        if pd.isna(val):
            return default
    except Exception:
        pass
    s = str(val).strip()
    return default if is_blank(s) else s


def _date_from_cell(val: Any) -> str:
    if val is None:
        return ""
    try:
        import pandas as pd
        if pd.isna(val):
            return ""
    except Exception:
        pass
    if hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d")
    m = re.search(r"\d{4}-\d{2}-\d{2}", str(val))
    return m.group(0) if m else ""


def scrape_jobspy_live(query: str, location: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """Live multi-platform scraping with JobSpy (Indeed, LinkedIn, Glassdoor)."""
    offers: List[Dict[str, Any]] = []
    try:
        from jobspy import scrape_jobs
    except Exception as e:
        print(f"Notice: jobspy unavailable: {e}")
        return offers

    loc_str = location.strip() or "France"
    terms = split_query_terms(query, max_terms=2) or [""]
    per_term = max(3, max_results // len(terms))
    seen_urls = set()

    for term in terms:
        search_term = term if "stage" in term.lower() or "intern" in term.lower() else f"Stage {term}".strip()
        try:
            df = scrape_jobs(
                site_name=["indeed", "linkedin", "glassdoor"],
                search_term=search_term,
                location=loc_str,
                results_wanted=per_term,
                country_indeed="France",
            )
        except Exception as e:
            print(f"Notice: Live scrape JobSpy error: {e}")
            continue
        if df is None or df.empty:
            continue

        for _, row in df.iterrows():
            title = _clean_cell(row.get("title"))
            company = _clean_cell(row.get("company"))
            job_url = _clean_cell(row.get("job_url_direct")) or _clean_cell(row.get("job_url"))
            if not title or not job_url.startswith(("http://", "https://")) or job_url in seen_urls:
                continue
            seen_urls.add(job_url)

            job_loc = _clean_cell(row.get("location"), loc_str)
            site = _clean_cell(row.get("site"), "Indeed").capitalize()
            desc = _clean_cell(row.get("description"))
            short_desc = desc[:600] + ("..." if len(desc) > 600 else "")

            offers.append({
                "title": title,
                "company": company,
                "location": job_loc,
                "contract": "Stage",
                "category": term or "Stage",
                "tags": extract_tech_tags(f"{title} {desc}"),
                "description": short_desc,
                "url": job_url,
                "date_posted": _date_from_cell(row.get("date_posted")),
                "source": f"JobSpy // {site}",
                "is_active": True,
                "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
    return offers


async def _run_tool(func, *args) -> List[Dict[str, Any]]:
    """Runs a blocking scraper in a thread with a hard timeout (the thread is abandoned on timeout)."""
    try:
        return await asyncio.wait_for(asyncio.to_thread(func, *args), timeout=TOOL_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        print(f"Notice: live tool {getattr(func, '__name__', func)} timed out after {TOOL_TIMEOUT_SECONDS}s")
    except Exception as e:
        print(f"Notice: live tool {getattr(func, '__name__', func)} failed: {e}")
    return []


async def execute_live_search_tools(query: str = "", location: str = "") -> List[Dict[str, Any]]:
    """
    Dynamically executes the enabled live search tools (no fixed registries):
    JobSpy (Indeed/LinkedIn/Glassdoor), DDGS on recruitment platforms and DDGS on corporate career portals.
    """
    settings = load_worker_settings()
    sources = {t["id"]: t for t in settings["sources"]}

    tasks = []
    if sources.get("jobspy_live", {}).get("enabled", True):
        tasks.append(_run_tool(scrape_jobspy_live, query, location, 8))
    if sources.get("ddgs_wttj_apec", {}).get("enabled", True):
        tasks.append(_run_tool(search_ddgs_live, query, location, sources["ddgs_wttj_apec"].get("target_sites", ""), 6))
    if sources.get("ddgs_corporate_labs", {}).get("enabled", True):
        tasks.append(_run_tool(search_ddgs_live, query, location, sources["ddgs_corporate_labs"].get("target_sites", ""), 6))

    results = await asyncio.gather(*tasks) if tasks else []
    all_live_offers: List[Dict[str, Any]] = [o for batch in results for o in batch]

    try:
        with STORE_LOCK:
            atomic_write_json(SEARCH_CACHE_FILE, all_live_offers)
    except Exception:
        pass

    return all_live_offers


def profile_query(profile: Optional[Dict[str, Any]] = None, max_domains: int = 3, max_skills: int = 3) -> str:
    """Search keywords derived from the CV profile (target domains first, then skills). Empty if no profile."""
    profile = profile if profile is not None else load_profile()
    domains = [d for d in profile.get("target_domains", []) if str(d).strip()]
    if domains:
        return ", ".join(domains[:max_domains])
    skills = [s for s in profile.get("technical_skills", []) if str(s).strip()]
    return ", ".join(skills[:max_skills])


async def fetch_all_registries(query: str = "") -> List[Dict[str, Any]]:
    """Worker entry point: live search using CV-derived keywords when no query is given."""
    query = query or profile_query()
    if not query:
        return []  # nothing to search for until a CV has been provided
    return await execute_live_search_tools(query, "France")
