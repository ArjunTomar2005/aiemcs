"""
AIEMCS - Equipment Decision Engine
Multi-step fallback search with intelligent ranking.

Step 1 → Exact match: same block + same time slot free
Step 2 → Same equipment type in any block
Step 3 → Similar specification / category
Step 4 → Nearest available time in same block

Processor ranking: i9 > i7 > i5 > i3
"""
from __future__ import annotations
import re
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from backend.models.db_models import EquipmentData, EquipmentUtilization


# ── Spec ranking tables ────────────────────────────────────────────────────────

PROCESSOR_RANK: Dict[str, int] = {
    'i9': 9, 'i7': 7, 'i5': 5, 'i3': 3,
    'ryzen 9': 9, 'ryzen 7': 7, 'ryzen 5': 5, 'ryzen 3': 3,
    'xeon': 8, 'core ultra 9': 9, 'core ultra 7': 7,
}

RAM_RANK: Dict[str, int] = {
    '128gb': 128, '64gb': 64, '32gb': 32, '16gb': 16, '8gb': 8, '4gb': 4,
}

GPU_RANK: Dict[str, int] = {
    'rtx 4090': 100, 'rtx 4080': 90, 'rtx 4070': 80, 'rtx 3090': 75,
    'rtx 3080': 70, 'rtx 3070': 65, 'rtx 3060': 55, 'rtx 3050': 45,
    'gtx 1080': 40, 'gtx 1070': 35, 'gtx 1660': 30, 'gtx 1060': 25,
    'rx 6800': 68, 'rx 6700': 58, 'rx 6600': 48,
}

ALL_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
ALL_SLOTS = [
    '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:00-12:00',
    '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00'
]


def _spec_score(model_details: str | None) -> int:
    """Compute a numeric rank for a model spec string. Higher = better."""
    if not model_details:
        return 0
    s = model_details.lower()
    score = 0
    for proc, rank in PROCESSOR_RANK.items():
        if proc in s:
            score += rank * 10
            break
    for ram, rank in RAM_RANK.items():
        if ram in s:
            score += rank
            break
    for gpu, rank in GPU_RANK.items():
        if gpu in s:
            score += rank * 5
            break
    if 'nvme' in s or 'ssd' in s:
        score += 10
    return score


def _get_busy_slots(db: Session, block_location: str) -> Dict[str, List[str]]:
    """
    Return dict of {day: [busy_slot, ...]} for a given location.
    """
    busy: Dict[str, List[str]] = {}
    rows = db.query(EquipmentUtilization).filter(
        EquipmentUtilization.block_location == block_location
    ).all()
    for row in rows:
        if row.activity and row.activity.lower() not in ('free', ''):
            day = (row.day or '').capitalize()
            if day not in busy:
                busy[day] = []
            # slot field may contain multiple comma-separated slots
            for s in (row.slot or '').split(','):
                s = s.strip()
                if s:
                    busy[day].append(s)
    return busy


def _get_free_slots(db: Session, block_location: str) -> Dict[str, List[str]]:
    """
    Return dict of {day: [free_slot, ...]} for a given location.
    All slots not marked busy are considered free.
    """
    busy = _get_busy_slots(db, block_location)
    free: Dict[str, List[str]] = {}
    for day in ALL_DAYS:
        busy_for_day = busy.get(day, [])
        free_slots = [s for s in ALL_SLOTS if s not in busy_for_day]
        if free_slots:
            free[day] = free_slots
    return free


def _is_location_free(db: Session, block_location: str,
                      day: Optional[str], slot: Optional[str]) -> bool:
    """Return True if the location is free at the requested day/slot."""
    if not day and not slot:
        return True
    busy = _get_busy_slots(db, block_location)
    if not day:
        return True
    busy_slots = busy.get(day.capitalize(), [])
    if not slot:
        # If no specific slot requested, check if any slot is free that day
        return len(busy_slots) < len(ALL_SLOTS)
    return slot not in busy_slots


def _find_nearest_free_slot(db: Session, block_location: str,
                             preferred_day: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    Find the next free slot at this location.
    Prefers the requested day first, then other days.
    """
    free = _get_free_slots(db, block_location)
    if not free:
        return None

    # Try preferred day first
    if preferred_day and preferred_day.capitalize() in free:
        day = preferred_day.capitalize()
        return {'day': day, 'slot': free[day][0]}

    # Otherwise return first available across all days
    for day in ALL_DAYS:
        if day in free and free[day]:
            return {'day': day, 'slot': free[day][0]}

    return None


def _format_free_slots(free_slots: Dict[str, List[str]], max_days: int = 3) -> str:
    """Format free slots dict into a readable string."""
    if not free_slots:
        return "No free slots found"
    parts = []
    for day in ALL_DAYS:
        if day in free_slots and max_days > 0:
            slots = free_slots[day]
            if len(slots) <= 3:
                parts.append(f"{day}: {', '.join(slots)}")
            else:
                parts.append(f"{day}: {', '.join(slots[:3])} (+{len(slots)-3} more)")
            max_days -= 1
    return " | ".join(parts) if parts else "No free slots found"


def _eq_to_dict(eq: EquipmentData, match_type: str,
                free_slots: Optional[Dict[str, List[str]]] = None,
                nearest: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    result = {
        'id':                      eq.id,
        'equipment_name':          eq.equipment_name,
        'equipment_category':      eq.equipment_category,
        'equipment_model_details': eq.equipment_model_details,
        'block_location':          eq.block_location,
        'working_status':          eq.working_status,
        'quantity':                eq.quantity,
        'match_type':              match_type,
        'free_slots':              free_slots or {},
        'free_slots_summary':      _format_free_slots(free_slots) if free_slots else 'Available',
        'suggested_day':           nearest['day']  if nearest else None,
        'suggested_slot':          nearest['slot'] if nearest else None,
    }
    return result


# ── Public API ─────────────────────────────────────────────────────────────────

class SearchQuery:
    """Parsed user query parameters."""
    def __init__(
        self,
        equipment_name:     Optional[str] = None,
        equipment_category: Optional[str] = None,
        block:              Optional[str] = None,
        day:                Optional[str] = None,
        slot:               Optional[str] = None,
        spec_keywords:      Optional[List[str]] = None,
        limit:              int = 5,
    ):
        self.equipment_name     = equipment_name
        self.equipment_category = equipment_category
        self.block              = block
        self.day                = day
        self.slot               = slot
        self.spec_keywords      = spec_keywords or []
        self.limit              = limit


def search_equipment(db: Session, query: SearchQuery) -> List[Dict[str, Any]]:
    """
    Multi-step equipment search with intelligent fallback.
    Returns a ranked list of equipment dicts with full availability info.
    """

    def base_query():
        q = db.query(EquipmentData).filter(
            EquipmentData.working_status.in_(['good', 'available'])
        )
        if query.equipment_name:
            q = q.filter(
                EquipmentData.equipment_name.ilike(f"%{query.equipment_name}%")
            )
        return q

    results: List[Dict[str, Any]] = []
    seen_ids: set = set()

    # ── STEP 1: Exact match — same block, time is free ─────────────────────────
    if query.block:
        step1 = (
            base_query()
            .filter(EquipmentData.block_location.like(f"{query.block}_%"))
            .all()
        )
        exact = [
            eq for eq in step1
            if _is_location_free(db, eq.block_location, query.day, query.slot)
        ]
        exact.sort(key=lambda e: _spec_score(e.equipment_model_details), reverse=True)
        for eq in exact[:query.limit]:
            free = _get_free_slots(db, eq.block_location)
            nearest = _find_nearest_free_slot(db, eq.block_location, query.day)
            results.append(_eq_to_dict(eq, 'exact', free, nearest))
            seen_ids.add(eq.id)

    if len(results) >= query.limit:
        return results

    # ── STEP 2: Same equipment type, any block ─────────────────────────────────
    step2 = base_query().all()
    available_any = [
        eq for eq in step2
        if _is_location_free(db, eq.block_location, query.day, query.slot)
        and eq.id not in seen_ids
    ]
    available_any.sort(key=lambda e: _spec_score(e.equipment_model_details), reverse=True)
    for eq in available_any:
        if len(results) >= query.limit:
            break
        free = _get_free_slots(db, eq.block_location)
        nearest = _find_nearest_free_slot(db, eq.block_location, query.day)
        results.append(_eq_to_dict(eq, 'same_category', free, nearest))
        seen_ids.add(eq.id)

    if len(results) >= query.limit:
        return results

    # ── STEP 3: Similar category ───────────────────────────────────────────────
    if query.equipment_category:
        step3 = (
            db.query(EquipmentData)
            .filter(
                EquipmentData.working_status.in_(['good', 'available']),
                EquipmentData.equipment_category.ilike(f"%{query.equipment_category}%")
            )
            .all()
        )
        step3.sort(key=lambda e: _spec_score(e.equipment_model_details), reverse=True)
        for eq in step3:
            if eq.id not in seen_ids and len(results) < query.limit:
                free = _get_free_slots(db, eq.block_location)
                nearest = _find_nearest_free_slot(db, eq.block_location, query.day)
                results.append(_eq_to_dict(eq, 'alternative', free, nearest))
                seen_ids.add(eq.id)

    if len(results) >= query.limit:
        return results

    # ── STEP 4: Nearest available time (relax time constraint) ─────────────────
    step4 = base_query().all()
    step4.sort(key=lambda e: _spec_score(e.equipment_model_details), reverse=True)
    for eq in step4:
        if eq.id not in seen_ids and len(results) < query.limit:
            free = _get_free_slots(db, eq.block_location)
            nearest = _find_nearest_free_slot(db, eq.block_location, query.day)
            results.append(_eq_to_dict(eq, 'nearest_time', free, nearest))
            seen_ids.add(eq.id)

    return results