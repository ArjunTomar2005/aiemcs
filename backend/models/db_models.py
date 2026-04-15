"""
AIEMCS - SQLAlchemy ORM Models
Mirrors the four tables defined in the schema.
"""
from datetime import date, datetime
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, Date,
    DateTime, ForeignKey, func
)
from backend.config import Base


class SourceData(Base):
    """Vendor / procurement source."""
    __tablename__ = "source_data"

    source_id  = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150))
    phone      = Column(String(20))
    room_duty  = Column(String(20))
    faculty    = Column(String(100))
    department = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())


class InchargeData(Base):
    """Lab incharge / admin user."""
    __tablename__ = "incharge_data"

    incharge_id   = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    email         = Column(String(150), unique=True)
    phone         = Column(String(20))
    room_duty     = Column(String(20))
    password_hash = Column(String(255))
    role          = Column(String(20), default="incharge")
    created_at    = Column(DateTime, server_default=func.now())


class EquipmentData(Base):
    """Core equipment inventory."""
    __tablename__ = "equipment_data"

    id                      = Column(Integer, primary_key=True, autoincrement=True)
    tag                     = Column(String(100), unique=True, nullable=False)
    equipment_name          = Column(String(150), nullable=False)
    equipment_category      = Column(String(100))
    equipment_model_details = Column(Text)
    unit_price              = Column(Numeric(12, 2))
    date_of_purchase        = Column(Date)
    quantity                = Column(Integer, default=1)
    working_status          = Column(String(50), default="good")
    faculty                 = Column(String(100))
    deparment               = Column(String(100))   # note: kept typo from schema
    block_location          = Column(String(20), index=True)
    source_id               = Column(Integer, ForeignKey("source_data.source_id",   ondelete="SET NULL"), nullable=True)
    incharge_id             = Column(Integer, ForeignKey("incharge_data.incharge_id", ondelete="SET NULL"), nullable=True)
    created_at              = Column(DateTime, server_default=func.now())
    updated_at              = Column(DateTime, server_default=func.now(), onupdate=func.now())


class EquipmentUtilization(Base):
    """Timetable / schedule records per room."""
    __tablename__ = "equipment_utilization"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    block_location = Column(String(20), nullable=False, index=True)
    type           = Column(String(50))
    day            = Column(String(20))
    slot           = Column(String(100))
    activity       = Column(String(200))
    incharge_id    = Column(Integer, ForeignKey("incharge_data.incharge_id", ondelete="SET NULL"), nullable=True)
    created_at     = Column(DateTime, server_default=func.now())
