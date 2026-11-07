from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import search, cv, letters, history, settings

app = FastAPI(
    title="InternReach API — Swiss Scientific Internship Engine",
    description="Backend API powering Agent Reach internship queries and multi-version motivation letters.",
    version="1.0.0"
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

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "InternReach Scientific Backend",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8008, reload=True)

