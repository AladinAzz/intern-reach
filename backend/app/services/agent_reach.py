import re
from typing import List, Dict, Any, Optional

from app.services.storage import load_profile, upsert_stored_jobs, load_stored_jobs
from app.services.registries import (
    execute_live_search_tools,
    extract_tech_tags,
    profile_query,
)

# Words that carry no search signal.
_QUERY_STOPWORDS = {"stage", "stages", "stagiaire", "intern", "internship", "pour", "les", "des", "une", "dans", "the", "and", "avec"}

# Greater-Paris aliases: a job in "Palaiseau" must match a "Paris / Île-de-France" search.
_IDF_TERMS = ("paris", "île-de-france", "ile-de-france", "idf", "saclay", "palaiseau", "versailles", "nanterre", "gennevilliers",
              "massy", "orsay", "gif-sur-yvette", "boulogne", "montrouge", "issy", "courbevoie", "la défense", "la defense", "vélizy", "velizy")
_IDF_DEPARTMENTS = re.compile(r"\b(?:75|77|78|91|92|93|94|95)\b")


def _word_in(haystack_lower: str, term: str) -> bool:
    return re.search(r"(?<![\w+#])" + re.escape(term.lower()) + r"(?![\w+#])", haystack_lower) is not None


def query_tokens(query: str) -> List[str]:
    tokens = re.findall(r"[\w+#]+", (query or "").lower().replace("&", " "))
    return [t for t in tokens if len(t) > 2 and t not in _QUERY_STOPWORDS]


def location_matches(target_loc: str, job_loc: str) -> bool:
    target = (target_loc or "").strip().lower()
    if not target:
        return True
    job = (job_loc or "").lower()
    if target in job:
        return True
    if any(t in target for t in _IDF_TERMS) or _IDF_DEPARTMENTS.search(target):
        if any(t in job for t in _IDF_TERMS) or _IDF_DEPARTMENTS.search(job):
            return True
    target_tokens = [t for t in re.findall(r"[a-zà-ÿ'-]+", target) if len(t) > 2]
    return any(tok in job for tok in target_tokens)


def calculate_ats_affinity(offer: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resume-vs-offer affinity computed only from real overlap between the CV and the posting.
    match_score is 0 when the CV provides nothing to compare with (the UI then hides the percentage).
    """
    skills = [str(s).strip() for s in profile.get("technical_skills", []) if str(s).strip()]
    domains = [str(d).strip().lower() for d in profile.get("target_domains", []) if str(d).strip()]
    offer_tags = [str(t) for t in (offer.get("tags") or [])]

    haystack = f"{offer.get('title') or ''} {offer.get('description') or ''} {' '.join(offer_tags)}".lower()

    matched = [s for s in skills if _word_in(haystack, s)]
    skills_lower = [s.lower() for s in skills]
    missing = [t for t in offer_tags if not any(t.lower() in us or us in t.lower() for us in skills_lower)]

    if not skills and not domains:
        score = 0
    else:
        skill_part = min(1.0, len(matched) / 3.0) * 60 if skills else 0
        domain_part = 25 if any(_word_in(haystack, d) or any(_word_in(haystack, w) for w in re.findall(r"[\wà-ÿ+#]{4,}", d)) for d in domains) else 0
        tag_part = (15 * len([t for t in offer_tags if t not in missing]) / len(offer_tags)) if offer_tags else 0
        score = int(max(10, min(99, round(skill_part + domain_part + tag_part))))

    offer["match_score"] = score
    offer["matched_skills"] = matched
    offer["missing_skills"] = missing[:4]
    return offer


class AgentReachService:
    async def search_internships_async(self, query: str = "", location: str = "") -> List[Dict[str, Any]]:
        """
        Unified live search:
        1. Live scraping/search through the enabled tools (JobSpy, DDGS recruitment sites, DDGS career portals).
        2. Persistence + de-duplication of every sighting in the local store.
        3. Selection of stored offers matching the location/keywords (fresh live hits always included).
        4. CV-vs-offer affinity scoring and newest-first ordering.
        """
        profile = load_profile()
        query = (query or "").strip() or profile_query(profile)
        target_loc = (location or "").strip()

        live_jobs: List[Dict[str, Any]] = []
        try:
            live_jobs = await execute_live_search_tools(query, target_loc)
        except Exception as e:
            print(f"Notice: Live search tools error: {e}")

        persisted = upsert_stored_jobs(live_jobs) if live_jobs else load_stored_jobs()

        # Fresh hits (identified by URL) bypass the keyword/location filters: the source engine already matched them.
        from app.services.storage import canonical_url
        live_urls = {canonical_url(j.get("url", "")) for j in live_jobs}

        q_tokens = query_tokens(query)
        selected: List[Dict[str, Any]] = []
        for job in persisted:
            if canonical_url(job.get("url", "")) in live_urls:
                selected.append(job)
                continue
            if not location_matches(target_loc, job.get("location", "")):
                continue
            if q_tokens:
                haystack = f"{job.get('title', '')} {job.get('company', '')} {job.get('description', '')} {' '.join(job.get('tags', []))}".lower()
                if not any(tok in haystack for tok in q_tokens):
                    continue
            selected.append(job)

        scored = [calculate_ats_affinity(dict(j), profile) for j in selected]
        scored.sort(key=lambda x: (str(x.get("date_posted") or "")[:10], x.get("match_score", 0)), reverse=True)
        return scored


agent_reach_service = AgentReachService()
