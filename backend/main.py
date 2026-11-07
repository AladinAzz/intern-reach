import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def _load_dotenv(path: str) -> None:
    """Minimal .env loader (KEY=VALUE lines); existing environment variables always win."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip().strip('"').strip("'")
                if key and value and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        pass


_load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.routers import search, cv, letters, history, settings, worker  # noqa: E402 (needs env loaded first)

# Only the local frontend may call the API from a browser (override with CORS_ORIGINS="https://a,https://b").
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:3005,http://127.0.0.1:3005").split(",")
    if o.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        from app.services.worker import ingestion_worker
        ingestion_worker.start_background_scheduler()
    except Exception as e:
        print(f"Notice: Background scheduler startup: {e}")
    yield
    # Shutdown
    try:
        from app.services.worker import ingestion_worker
        ingestion_worker.stop_background_scheduler()
    except Exception:
        pass


app = FastAPI(
    title="InternReach API — Swiss Scientific Internship Engine",
    description="Backend API powering live multi-source search, CV analysis, letter studio and the autonomous liveness worker.",
    version="1.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # no cookies/sessions are used; wildcard+credentials is also invalid per the CORS spec
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(search.router)
app.include_router(cv.router)
app.include_router(letters.router)
app.include_router(history.router)
app.include_router(settings.router)
app.include_router(worker.router)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "InternReach Scientific Backend",
        "version": "1.2.0",
    }


if __name__ == "__main__":
    import uvicorn
    # Loopback only: this API has no authentication and manages private data/API keys.
    uvicorn.run("main:app", host="127.0.0.1", port=8008, reload=True)
