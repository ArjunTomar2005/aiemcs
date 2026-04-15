"""
AIEMCS - Authentication Service
JWT token generation and verification, bcrypt password hashing.
"""
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE
from backend.models.db_models import InchargeData


def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def create_access_token(data: dict, expires_minutes: int = TOKEN_EXPIRE) -> str:
    """Create a signed JWT access token."""
    payload = data.copy()
    expire  = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload or None."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def authenticate_incharge(db: Session, email: str, password: str) -> Optional[InchargeData]:
    """
    Look up an incharge by email and verify their password.
    Returns the InchargeData record or None if authentication fails.
    """
    incharge = db.query(InchargeData).filter(InchargeData.email == email).first()
    if not incharge:
        return None
    if not incharge.password_hash:
        return None
    if not verify_password(password, incharge.password_hash):
        return None
    return incharge


def get_current_incharge(db: Session, token: str) -> Optional[InchargeData]:
    """Extract incharge from JWT token."""
    payload = decode_token(token)
    if payload is None:
        return None
    incharge_id = payload.get("sub")
    if incharge_id is None:
        return None
    return db.query(InchargeData).filter(InchargeData.incharge_id == int(incharge_id)).first()
