"""
AIEMCS - Configuration & Database Session
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# ── Database URL ───────────────────────────────────────────────────────────────
DB_USER     = os.getenv("DB_USER",     "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = os.getenv("DB_PORT",     "3306")
DB_NAME     = os.getenv("DB_NAME",     "aiemcs")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ── Engine & Session ───────────────────────────────────────────────────────────
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    """Dependency: yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── App settings ───────────────────────────────────────────────────────────────
SECRET_KEY   = os.getenv("SECRET_KEY", "aiemcs-secret-change-in-production")
ALGORITHM    = "HS256"
TOKEN_EXPIRE = 60 * 24   # minutes

UPLOAD_DIR   = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── Tesseract path (Windows users set this) ────────────────────────────────────
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")

# ── AI Keys ───────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
USE_AI         = bool(OPENAI_API_KEY or GEMINI_API_KEY)