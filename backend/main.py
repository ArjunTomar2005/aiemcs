"""
AIEMCS - AI Powered Equipment Monitoring and Control System
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.config import engine
from backend.models.db_models import Base

# Import routers
from backend.routers.auth      import router as auth_router
from backend.routers.chat      import router as chat_router
from backend.routers.lab       import router as lab_router
from backend.routers.timetable import router as timetable_router

# ── App setup ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AIEMCS - AI Powered Equipment Monitoring and Control System",
    description=(
        "Intelligent infrastructure management platform for institutional equipment. "
        "Provides chatbot-driven equipment availability queries, lab management, "
        "timetable OCR processing, and role-based access control."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # In production: restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database: create tables if they don't exist ────────────────────────────────

@app.on_event("startup")
async def startup():
    """Auto-create tables on first run (if not already created via schema.sql)."""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables verified.")
    except Exception as e:
        print(f"⚠️  DB startup warning: {e}")

# ── Routes ─────────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(lab_router)
app.include_router(timetable_router)

# ── Static frontend ────────────────────────────────────────────────────────────

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health_check():
    """Returns system health status."""
    return {"status": "ok", "system": "AIEMCS v1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
