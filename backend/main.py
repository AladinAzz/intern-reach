from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import search, cv, letters, history, settings, worker

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
    description="Backend API powering multi-source registries, JobSpy scraper, and autonomous liveness worker.",
    version="1.1.0",
    lifespan=lifespan
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        "version": "1.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8008, reload=True)
