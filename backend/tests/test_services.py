import asyncio

import httpx
import pytest

from app.services import agent_reach, job_extractor, worker
from app.services.agent_reach import calculate_ats_affinity, location_matches, query_tokens, agent_reach_service
from app.services.cv_parser import parse_cv_to_profile, extract_text_from_pdf, CvExtractionError
from app.services.registries import extract_tech_tags, is_listing_page, split_query_terms
from app.services.storage import (
    are_jobs_duplicate,
    canonical_url,
    load_history,
    load_profile,
    load_stored_jobs,
    normalize_profile,
    sanitize_job_dict,
    save_profile,
    stable_job_id,
    upsert_stored_jobs,
    update_history_status,
    delete_history_entry,
    add_history_entry,
)

SAMPLE_CV = """
Jean Dupont
Email: jean.dupont@telecom-paris.fr
Tel: 06 12 34 56 78
Formation: Diplôme d'ingénieur spécialité Systèmes Embarqués et IA.
Compétences: C++, PyTorch, OpenCV, Linux Embarqué, FreeRTOS, ROS 2, FPGA, VHDL, TensorRT.
Projets:
- Déploiement d'un modèle YOLOv8 sur NVIDIA Jetson Nano avec quantification INT8.
"""


# ----------------------------------------------------------------------------- CV parsing
def test_cv_parser_extracts_identity_and_skills():
    profile = parse_cv_to_profile(SAMPLE_CV)
    assert profile["email"] == "jean.dupont@telecom-paris.fr"
    assert "06 12 34 56 78" in profile["phone"]
    assert profile["full_name"] == "Jean Dupont"
    for skill in ("C++", "PyTorch", "ROS 2", "TensorRT"):
        assert skill in profile["technical_skills"]
    assert "Systèmes Embarqués" in profile["education"]


def test_cv_parser_never_reuses_previous_profile():
    save_profile({"full_name": "Someone Else", "education": "Old degree", "target_domains": ["Enseignement"],
                  "technical_skills": ["Word"], "key_projects": [{"title": "Old", "desc": "x"}]})
    profile = parse_cv_to_profile("Marie Curie\nmarie@lab.fr\nCompétences\nRadioactivité\nChimie\nExpérience\nLabo")
    assert profile["target_domains"] == []
    assert profile["key_projects"] == []
    assert "Word" not in profile["technical_skills"]
    assert profile["technical_skills"] == ["Radioactivité", "Chimie"]


def test_cv_parser_international_phone():
    assert "+213 555 12 34 56" in parse_cv_to_profile("Karim Benali\nTel +213 555 12 34 56\n")["phone"]


def test_pdf_extraction_rejects_garbage():
    with pytest.raises(CvExtractionError):
        extract_text_from_pdf(b"%PDF-1.4 definitely not a pdf")


def test_default_profile_is_empty_not_fake():
    p = load_profile()
    assert p["full_name"] == "" and p["technical_skills"] == [] and p["target_domains"] == [] and p["key_projects"] == []


def test_normalize_profile_survives_garbage():
    p = normalize_profile({"technical_skills": "oops", "key_projects": [None, "x", {"title": "T"}], "full_name": None})
    assert p["technical_skills"] == [] and p["full_name"] == ""
    assert p["key_projects"] == [{"title": "x", "desc": ""}, {"title": "T", "desc": ""}]


# ----------------------------------------------------------------------------- de-duplication
def test_canonical_url_keeps_job_identity_params():
    a = canonical_url("https://fr.indeed.com/viewjob?jk=AAA&utm_source=x")
    b = canonical_url("https://fr.indeed.com/viewjob?jk=BBB")
    assert a != b
    assert canonical_url("https://fr.indeed.com/viewjob?jk=AAA&utm_source=x#frag") == canonical_url("https://www.fr.indeed.com/viewjob/?jk=AAA")


def test_distinct_indeed_jobs_are_not_merged():
    j1 = {"title": "Stage FPGA", "company": "Alpha", "location": "Paris", "url": "https://fr.indeed.com/viewjob?jk=111"}
    j2 = {"title": "Stage Cuisinier", "company": "Beta", "location": "Lyon", "url": "https://fr.indeed.com/viewjob?jk=222"}
    assert not are_jobs_duplicate(j1, j2)
    stored = upsert_stored_jobs([j1, j2])
    assert len(stored) == 2


def test_same_posting_is_merged_across_sightings():
    j1 = {"title": "STAGE - Ingénieur.e Linux Embarqué H/F", "company": "KNDS France Systems", "location": "Toulouse",
          "url": "https://fr.indeed.com/viewjob?jk=12345"}
    j2 = {"title": "Ingénieur Linux Embarqué (F/H)", "company": "KNDS", "location": "Toulouse",
          "url": "https://fr.indeed.com/viewjob?jk=12345&utm_campaign=a"}
    assert are_jobs_duplicate(j1, j2)
    assert len(upsert_stored_jobs([j1])) == 1
    assert len(upsert_stored_jobs([j2])) == 1


def test_same_company_title_different_city_not_duplicate():
    a = {"title": "Stage Vision par ordinateur", "company": "Thales", "location": "Toulouse", "url": "https://t.com/1"}
    b = {"title": "Stage Vision par ordinateur", "company": "Thales", "location": "Paris", "url": "https://t.com/2"}
    assert not are_jobs_duplicate(a, b)


def test_placeholder_company_never_merges_unrelated_offers():
    a = {"title": "Stage vision embarquée", "company": "Entreprise non précisée", "location": "France", "url": "https://x.org/a-long-path-1"}
    b = {"title": "Stage vision embarquée avancée", "company": "Entreprise non précisée", "location": "France", "url": "https://y.org/b-long-path-2"}
    assert not are_jobs_duplicate(a, b)


def test_sanitize_removes_nan_and_assigns_stable_id():
    job = {"title": "nan", "company": None, "url": "nan", "description": "nan", "date_posted": "garbage"}
    clean = sanitize_job_dict(dict(job))
    assert clean["url"].startswith("https://www.google.com/search?q=")
    assert "nan" not in clean["title"].lower().split() and "nan" not in clean["description"].lower().split()
    assert clean["tags"] == [] and clean["date_estimated"] is True
    assert clean["id"] == stable_job_id(clean) == sanitize_job_dict(dict(job))["id"]


def test_ids_unique_for_distinct_urls():
    ids = {stable_job_id({"url": f"https://x.org/job/{i}"}) for i in range(200)}
    assert len(ids) == 200


def test_estimated_date_does_not_override_real_date():
    real = {"title": "Stage Alpha", "company": "Acme", "location": "Paris", "url": "https://acme.com/jobs/12345", "date_posted": "2026-01-15"}
    upsert_stored_jobs([real])
    again = {"title": "Stage Alpha", "company": "Acme", "location": "Paris", "url": "https://acme.com/jobs/12345", "date_posted": ""}
    stored = upsert_stored_jobs([again])
    assert stored[0]["date_posted"] == "2026-01-15" and stored[0]["date_estimated"] is False


# ----------------------------------------------------------------------------- scoring / matching
def test_affinity_short_skills_do_not_match_everything():
    offer = {"title": "Stage comptabilité", "description": "Gestion de la facturation clients", "tags": []}
    res = calculate_ats_affinity(dict(offer), {"technical_skills": ["C", "R", "Go"], "target_domains": []})
    assert res["matched_skills"] == []


def test_affinity_real_overlap_and_empty_profile():
    offer = {"title": "Stage FPGA", "description": "VHDL et C++ sur Vivado", "tags": ["VHDL", "C++", "Vivado"]}
    res = calculate_ats_affinity(dict(offer), {"technical_skills": ["VHDL", "C++"], "target_domains": ["FPGA"]})
    assert set(res["matched_skills"]) == {"VHDL", "C++"} and res["missing_skills"] == ["Vivado"]
    assert 50 < res["match_score"] <= 99
    assert calculate_ats_affinity(dict(offer), {})["match_score"] == 0


def test_affinity_tolerates_missing_fields():
    res = calculate_ats_affinity({"title": None, "description": None, "tags": None}, {"technical_skills": ["Python"]})
    assert res["matched_skills"] == []


def test_location_matching():
    assert location_matches("", "Anywhere")
    assert location_matches("Paris, Île-de-France", "Palaiseau (91)")
    assert location_matches("Paris", "Gennevilliers, 92")
    assert not location_matches("Toulouse", "Lyon")
    assert not location_matches("Lyon", "Paris 75")
    assert location_matches("Toulouse", "Toulouse, Occitanie")


def test_query_tokens_and_terms():
    assert query_tokens("Stage Systèmes embarqués, C++ & IA") == ["systèmes", "embarqués", "c++"]
    assert split_query_terms("a, b ; c / d", max_terms=2) == ["a", "b"]
    assert len(split_query_terms("x" * 500)[0]) == 80


def test_extract_tech_tags():
    tags = extract_tech_tags("Stage C++ et PyTorch pour déploiement TensorRT sur Jetson Orin", profile={"technical_skills": []})
    assert {"C++", "PyTorch", "TensorRT"} <= set(tags)
    assert "C" not in extract_tech_tags("code en C++ uniquement", profile={"technical_skills": []})
    assert extract_tech_tags("Poste de comptable", profile={"technical_skills": []}) == []
    assert "Comptabilité" in extract_tech_tags("Notions de comptabilité", profile={"technical_skills": ["Comptabilité"]})


def test_listing_pages_are_filtered_but_postings_kept():
    assert is_listing_page("https://fr.indeed.com/q-stage-groupe-atlantic-emplois.html?vjk=1")
    assert is_listing_page("https://fr.jooble.org/emploi-stage-ingenieur")
    assert is_listing_page("https://www.example.com/emplois")
    assert not is_listing_page("https://www.apec.fr/candidat/recherche-emploi.html/emploi/detail-offre/178")
    assert not is_listing_page("https://www.welcometothejungle.com/fr/companies/x/jobs/stage-ia_paris")


# ----------------------------------------------------------------------------- search pipeline (live tools stubbed)
async def test_search_pipeline_persists_scores_and_sorts(monkeypatch):
    save_profile({"full_name": "T", "technical_skills": ["Python"], "target_domains": ["data"]})
    live = [
        {"title": "Stage Data Python", "company": "A", "location": "Lyon", "url": "https://a.com/jobs/aaaaaaa", "date_posted": "2026-11-01", "description": "Python et SQL pour la data" * 3},
        {"title": "Stage Data Engineer", "company": "B", "location": "Lyon", "url": "https://b.com/jobs/bbbbbbb", "date_posted": "2026-11-05", "description": "Pipelines data" * 4},
    ]

    async def fake_tools(query, location):
        return [dict(j) for j in live]

    monkeypatch.setattr(agent_reach, "execute_live_search_tools", fake_tools)
    res = await agent_reach_service.search_internships_async("data", "")
    assert [r["company"] for r in res] == ["B", "A"]  # newest first
    assert len({r["id"] for r in res}) == 2
    assert res[1]["matched_skills"] == ["Python"]
    assert len(load_stored_jobs()) == 2  # persisted

    # Second search: stored offers are served even when live tools return nothing.
    async def no_tools(query, location):
        return []
    monkeypatch.setattr(agent_reach, "execute_live_search_tools", no_tools)
    again = await agent_reach_service.search_internships_async("data", "Lyon")
    assert len(again) == 2
    assert await agent_reach_service.search_internships_async("data", "Toulouse") == []
    assert await agent_reach_service.search_internships_async("zzzqqq", "") == []


async def test_search_never_fabricates_offers_when_live_tools_empty(monkeypatch, fake_llm):
    async def no_tools(query, location):
        return []
    monkeypatch.setattr(agent_reach, "execute_live_search_tools", no_tools)
    fake_llm.reply = '[{"title":"Fake","company":"Fake","url":"https://fake"}]'
    assert await agent_reach_service.search_internships_async("anything", "Paris") == []
    assert fake_llm.calls == []


# ----------------------------------------------------------------------------- history store
def test_history_crud_semantics():
    h = add_history_entry({"job_title": "A", "status": "bogus"})
    assert h[0]["status"] == "Enregistré"
    h = add_history_entry({"job_title": "B"})
    ids = [x["id"] for x in h]
    assert len(set(ids)) == 2
    assert update_history_status("nope", "Refusé") is None
    assert update_history_status(ids[0], "Refusé")[0]["status"] == "Refusé"
    assert delete_history_entry("nope") is None
    # ids stay unique even after deleting then re-adding (the old len()+1 scheme collided).
    delete_history_entry(ids[1])
    new_ids = [x["id"] for x in add_history_entry({"job_title": "C"})]
    assert len(set(new_ids)) == len(new_ids)


def test_atomic_writes_leave_no_temp_files():
    import os
    from app.services.storage import DATA_DIR
    upsert_stored_jobs([{"title": "Stage X", "company": "Y", "url": "https://y.com/job/1234567"}])
    assert not [f for f in os.listdir(DATA_DIR) if f.startswith(".tmp-")]


# ----------------------------------------------------------------------------- SSRF guard
@pytest.mark.parametrize("url", [
    "http://127.0.0.1/x", "http://localhost/x", "http://[::1]/x", "http://0.0.0.0/x", "http://10.0.0.5/x",
    "http://192.168.1.1/x", "http://169.254.169.254/latest/meta-data/", "http://[::ffff:127.0.0.1]/x",
    "http://172.16.0.1/", "file:///etc/passwd", "ftp://example.com/", "http://user:pw@8.8.8.8/", "http://8.8.8.8:8008/",
    "http://service.internal/", "http://printer.local/", "", "not a url",
])
def test_is_safe_url_blocks(url):
    assert job_extractor.is_safe_url(url) is False


def test_is_safe_url_allows_public_ip():
    assert job_extractor.is_safe_url("https://8.8.8.8/") is True


async def test_fetch_blocks_redirect_to_private_network(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "public.test":
            return httpx.Response(302, headers={"location": "http://127.0.0.1:8008/api/settings"})
        return httpx.Response(200, text="SECRET " * 50)

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(job_extractor.httpx, "AsyncClient", lambda **kw: real_client(transport=transport, **kw))
    monkeypatch.setattr(job_extractor, "is_safe_url", lambda u: "public.test" in u)
    with pytest.raises(job_extractor.ExtractionError) as exc:
        await job_extractor._fetch_page_text("https://public.test/job")
    assert exc.value.status_code == 400


async def test_import_without_input_raises():
    with pytest.raises(job_extractor.ExtractionError) as exc:
        await job_extractor.job_extractor.extract_from_url_or_text()
    assert exc.value.status_code == 422


async def test_import_text_without_llm_extracts_only_real_facts(no_llm):
    offer = await job_extractor.job_extractor.extract_from_url_or_text(raw_text="Stage Analyste financier chez Axa à Lyon. Excel et SQL exigés. Durée 6 mois.")
    assert "Axa" in offer["company"] or offer["company"] == ""
    assert "Excel" in offer["tags"] and "SQL" in offer["tags"]
    assert "PyTorch" not in offer["tags"] and "C++" not in offer["tags"]  # nothing invented


async def test_import_never_trusts_llm_url(fake_llm):
    fake_llm.reply = '{"title":"Stage X","company":"Y","location":"Z","tags":["a"],"description":"d","url":"javascript:alert(1)"}'
    offer = await job_extractor.job_extractor.extract_from_url_or_text(raw_text="Stage X chez Y " * 10)
    assert offer["url"] == ""


# ----------------------------------------------------------------------------- liveness
def _client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)


async def test_liveness_verdicts(monkeypatch):
    monkeypatch.setattr(worker, "is_safe_url", lambda u: True)

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/gone":
            return httpx.Response(404)
        if path == "/blocked":
            return httpx.Response(403)
        if path == "/flaky":
            return httpx.Response(503)
        if path == "/head405":
            return httpx.Response(405) if request.method == "HEAD" else httpx.Response(200)
        if path == "/moved":
            return httpx.Response(301, headers={"location": "/ok"})
        return httpx.Response(200)

    async with _client(handler) as c:
        assert await worker.check_url_liveness("https://s.test/ok", c) is True
        assert await worker.check_url_liveness("https://s.test/gone", c) is False
        assert await worker.check_url_liveness("https://s.test/blocked", c) is None  # bot-blocked != closed
        assert await worker.check_url_liveness("https://s.test/flaky", c) is None
        assert await worker.check_url_liveness("https://s.test/head405", c) is True
        assert await worker.check_url_liveness("https://s.test/moved", c) is True
        assert await worker.check_url_liveness("", c) is None


async def test_liveness_refuses_private_targets():
    async with _client(lambda r: httpx.Response(200)) as c:
        assert await worker.check_url_liveness("http://127.0.0.1:8008/health", c) is None


async def test_liveness_update_does_not_clobber_concurrent_additions():
    upsert_stored_jobs([{"title": "Stage One", "company": "A", "url": "https://a.com/jobs/1111111"}])
    snapshot = load_stored_jobs()
    # A job is added while the (slow) network sweep is running...
    upsert_stored_jobs([{"title": "Stage Two", "company": "B", "url": "https://b.com/jobs/2222222"}])
    # ...then the sweep result is applied on top of the *current* store.
    from app.services.storage import update_jobs_liveness
    final = update_jobs_liveness({snapshot[0]["id"]: False}, "2026-11-07 10:00")
    assert len(final) == 2
    assert {j["company"]: j.get("is_active") for j in final}["A"] is False


async def test_inconclusive_verdict_keeps_previous_state():
    upsert_stored_jobs([{"title": "Stage One", "company": "A", "url": "https://a.com/jobs/1111111", "is_active": True}])
    jid = load_stored_jobs()[0]["id"]
    from app.services.storage import update_jobs_liveness
    assert update_jobs_liveness({jid: None}, "t")[0]["is_active"] is True
