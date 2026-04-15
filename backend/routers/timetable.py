"""
AIEMCS - Timetable Upload & OCR Router
POST /timetable/upload
"""
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.config import get_db, UPLOAD_DIR
from backend.models.db_models import EquipmentUtilization
from backend.schemas.schemas import TimetableResponse, TimetableEntry
from backend.services.auth_service import decode_token
from backend.services.timetable_ocr import (
    OCR_AVAILABLE,
    process_timetable_image,
    mock_timetable_parse,
)

router = APIRouter(prefix="/timetable", tags=["Timetable"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".pdf"}


def require_auth(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    payload = decode_token(authorization.split(" ", 1)[1])
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    return payload


@router.post("/upload", response_model=TimetableResponse, summary="Upload timetable image for OCR processing")
async def upload_timetable(
    file: UploadFile = File(..., description="Timetable image (JPG, PNG, BMP, TIFF)"),
    location: str = Form(..., description="Block location e.g. E_316"),
    incharge_id: Optional[int] = Form(default=None),
    db: Session = Depends(get_db),
    _auth = Depends(require_auth),
):
    """
    Upload a timetable image.
    Pipeline: image → OCR → parse → store in equipment_utilization table.
    """
    # Validate extension
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not supported. Allowed: {ALLOWED_EXTENSIONS}"
        )

    # Save uploaded file
    save_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, save_name)

    contents = await file.read()
    with open(save_path, "wb") as f:
        f.write(contents)

    # OCR processing
    try:
        if OCR_AVAILABLE:
            raw_text, entries = process_timetable_image(save_path, location)
        else:
            raw_text, entries = mock_timetable_parse(location)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

    # Persist to DB
    saved = 0
    for entry in entries:
        row = EquipmentUtilization(
            block_location=entry.get("room") or location,
            type="lab",
            day=entry.get("day"),
            slot=entry.get("slot"),
            activity=entry.get("activity"),
            incharge_id=incharge_id,
        )
        db.add(row)
        saved += 1

    db.commit()

    return TimetableResponse(
        location=location,
        entries=[TimetableEntry(**{k: v for k, v in e.items() if k in TimetableEntry.model_fields}) for e in entries],
        raw_text=raw_text[:2000],  # Truncate for response
        saved=saved,
    )
