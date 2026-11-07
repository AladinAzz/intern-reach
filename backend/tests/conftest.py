import os
import shutil
import tempfile

import pytest

# IMPORTANT: must run before any `app.*` import so that storage.DATA_DIR points at a throw-away directory
# (the test-suite must never read or overwrite the user's real profile / history / API keys).
_TMP_DATA_DIR = tempfile.mkdtemp(prefix="intern-reach-tests-")
os.environ["INTERN_REACH_DATA_DIR"] = _TMP_DATA_DIR
for _var in ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
    os.environ.pop(_var, None)


@pytest.fixture(autouse=True)
def clean_data_dir():
    """Every test starts with an empty data directory."""
    for name in os.listdir(_TMP_DATA_DIR):
        path = os.path.join(_TMP_DATA_DIR, name)
        if os.path.isfile(path):
            os.unlink(path)
    yield


@pytest.fixture
def no_llm(monkeypatch):
    """Simulates an unreachable LLM provider (no network, deterministic fallbacks)."""
    from app.services import letter_generator as lg

    async def _boom(prompt, system_prompt=""):
        raise lg.LLMError("offline (test)")

    monkeypatch.setattr(lg.letter_generator, "call_llm_checked", _boom)
    return lg.letter_generator


@pytest.fixture
def fake_llm(monkeypatch):
    """Scripted LLM: set `fake_llm.reply` to the text each call should return."""
    from app.services import letter_generator as lg

    class Script:
        reply = ""
        calls = []

    async def _reply(prompt, system_prompt=""):
        Script.calls.append(prompt)
        return Script.reply

    Script.calls = []
    monkeypatch.setattr(lg.letter_generator, "call_llm_checked", _reply)
    return Script


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TMP_DATA_DIR, ignore_errors=True)

