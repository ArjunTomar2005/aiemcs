"""
AIEMCS - Authentication Router
POST /login
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.config import get_db
from backend.schemas.schemas import LoginRequest, LoginResponse
from backend.services.auth_service import authenticate_incharge, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse, summary="Incharge login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a lab incharge with email + password.
    Returns a JWT bearer token on success.
    """
    incharge = authenticate_incharge(db, payload.email, payload.password)
    if not incharge:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": str(incharge.incharge_id), "role": incharge.role})
    return LoginResponse(
        access_token=token,
        incharge_id=incharge.incharge_id,
        name=incharge.name,
        role=incharge.role or "incharge",
    )
