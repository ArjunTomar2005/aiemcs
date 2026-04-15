"""
AIEMCS - Lab Management Router
Equipment CRUD, incharge management.
Protected by JWT.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from backend.config import get_db, DATABASE_URL
from backend.models.db_models import EquipmentData, InchargeData, EquipmentUtilization
from backend.schemas.schemas import (
    EquipmentCreate, EquipmentUpdate, EquipmentOut,
    InchargeCreate, InchargeOut,
    UtilizationOut,
)
from backend.services.auth_service import decode_token, hash_password

router = APIRouter(prefix="/lab", tags=["Lab Management"])


# ── Dependency: verify JWT ─────────────────────────────────────────────────────

def require_auth(authorization: Optional[str] = Header(default=None)):
    """Validate Bearer token from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")
    return payload


# ── Equipment endpoints ────────────────────────────────────────────────────────

@router.get("/equipment", response_model=List[EquipmentOut], summary="List all equipment")
def list_equipment(
    skip: int = 0,
    limit: int = 50,
    block: Optional[str] = None,
    category: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    _auth = Depends(require_auth),
):
    """List equipment with optional filters. Paginated."""
    q = db.query(EquipmentData)
    if block:
        q = q.filter(EquipmentData.block_location.like(f"{block}_%"))
    if category:
        q = q.filter(EquipmentData.equipment_category.ilike(f"%{category}%"))
    if status_filter:
        q = q.filter(EquipmentData.working_status == status_filter)
    return q.offset(skip).limit(limit).all()


@router.post("/equipment/add", response_model=EquipmentOut, summary="Add new equipment", status_code=201)
def add_equipment(
    payload: EquipmentCreate,
    db: Session = Depends(get_db),
    _auth = Depends(require_auth),
):
    """Add a new equipment record."""
    existing = db.query(EquipmentData).filter(EquipmentData.tag == payload.tag).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Equipment with tag '{payload.tag}' already exists.")

    eq = EquipmentData(**payload.model_dump())
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq


@router.put("/equipment/update/{equipment_id}", response_model=EquipmentOut, summary="Update equipment")
def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdate,
    db: Session = Depends(get_db),
    _auth = Depends(require_auth),
):
    """Partially update an equipment record."""
    eq = db.query(EquipmentData).filter(EquipmentData.id == equipment_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found.")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(eq, field, value)

    db.commit()
    db.refresh(eq)
    return eq


@router.delete("/equipment/{equipment_id}", summary="Delete equipment")
def delete_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    _auth = Depends(require_auth),
):
    """Delete an equipment record."""
    eq = db.query(EquipmentData).filter(EquipmentData.id == equipment_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found.")
    db.delete(eq)
    db.commit()
    return {"message": "Equipment deleted successfully."}


# ── Incharge management ────────────────────────────────────────────────────────

@router.get("/incharges", response_model=List[InchargeOut], summary="List incharges")
def list_incharges(
    skip: int = 0, limit: int = 50,
    db: Session = Depends(get_db),
    _auth = Depends(require_auth),
):
    return db.query(InchargeData).offset(skip).limit(limit).all()


@router.post("/incharges/add", response_model=InchargeOut, status_code=201, summary="Add incharge")
def add_incharge(
    payload: InchargeCreate,
    db: Session = Depends(get_db),
    _auth = Depends(require_auth),
):
    existing = db.query(InchargeData).filter(InchargeData.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")

    data = payload.model_dump()
    plain_pw = data.pop("password")
    data["password_hash"] = hash_password(plain_pw)

    inc = InchargeData(**data)
    db.add(inc)
    db.commit()
    db.refresh(inc)
    return inc


# ── Utilization / schedule ─────────────────────────────────────────────────────

@router.get("/schedule", response_model=List[UtilizationOut], summary="View utilization schedule")
def view_schedule(
    block_location: Optional[str] = None,
    day: Optional[str] = None,
    db: Session = Depends(get_db),
    _auth = Depends(require_auth),
):
    q = db.query(EquipmentUtilization)
    if block_location:
        q = q.filter(EquipmentUtilization.block_location == block_location)
    if day:
        q = q.filter(EquipmentUtilization.day.ilike(day))
    return q.limit(200).all()
