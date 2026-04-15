"""
AIEMCS - Pydantic Schemas (request / response models)
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator


# ── Auth ───────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    incharge_id: int
    name: str
    role: str


# ── Source ─────────────────────────────────────────────────────────────────────

class SourceBase(BaseModel):
    source_id:  int
    name:       str
    email:      Optional[str] = None
    phone:      Optional[str] = None
    room_duty:  Optional[str] = None
    faculty:    Optional[str] = None
    department: Optional[str] = None

class SourceCreate(SourceBase):
    pass

class SourceOut(SourceBase):
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ── Incharge ───────────────────────────────────────────────────────────────────

class InchargeCreate(BaseModel):
    incharge_id: int
    name:        str
    email:       str
    phone:       Optional[str] = None
    room_duty:   Optional[str] = None
    password:    str

class InchargeOut(BaseModel):
    incharge_id: int
    name:        str
    email:       str
    phone:       Optional[str] = None
    room_duty:   Optional[str] = None
    role:        str
    created_at:  Optional[datetime] = None
    model_config = {"from_attributes": True}


# ── Equipment ──────────────────────────────────────────────────────────────────

class EquipmentBase(BaseModel):
    tag:                     str
    equipment_name:          str
    equipment_category:      Optional[str] = None
    equipment_model_details: Optional[str] = None
    unit_price:              Optional[float] = None
    date_of_purchase:        Optional[date]  = None
    quantity:                Optional[int]   = 1
    working_status:          Optional[str]   = "good"
    faculty:                 Optional[str]   = None
    deparment:               Optional[str]   = None
    block_location:          Optional[str]   = None
    source_id:               Optional[int]   = None
    incharge_id:             Optional[int]   = None

class EquipmentCreate(EquipmentBase):
    pass

class EquipmentUpdate(BaseModel):
    equipment_name:          Optional[str]   = None
    equipment_category:      Optional[str]   = None
    equipment_model_details: Optional[str]   = None
    unit_price:              Optional[float] = None
    quantity:                Optional[int]   = None
    working_status:          Optional[str]   = None
    block_location:          Optional[str]   = None
    incharge_id:             Optional[int]   = None

class EquipmentOut(EquipmentBase):
    id:         int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ── Utilization ────────────────────────────────────────────────────────────────

class UtilizationBase(BaseModel):
    block_location: str
    type:           Optional[str] = None
    day:            Optional[str] = None
    slot:           Optional[str] = None
    activity:       Optional[str] = None
    incharge_id:    Optional[int] = None

class UtilizationCreate(UtilizationBase):
    pass

class UtilizationOut(UtilizationBase):
    id:         int
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ── Chat ───────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class EquipmentResult(BaseModel):
    id:                      int
    equipment_name:          str
    equipment_category:      Optional[str]
    equipment_model_details: Optional[str]
    block_location:          Optional[str]
    working_status:          Optional[str]
    quantity:                Optional[int]
    match_type:              str   # exact / same_category / alternative / nearest_time

class ChatResponse(BaseModel):
    answer:    str
    results:   List[EquipmentResult] = []
    intent:    Optional[str]         = None


# ── Timetable OCR ──────────────────────────────────────────────────────────────

class TimetableEntry(BaseModel):
    day:      str
    slot:     str
    activity: str
    room:     Optional[str] = None

class TimetableResponse(BaseModel):
    location:   str
    entries:    List[TimetableEntry]
    raw_text:   Optional[str] = None
    saved:      int = 0
