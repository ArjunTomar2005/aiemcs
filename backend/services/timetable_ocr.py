"""
AIEMCS - Timetable OCR Service
Processes uploaded timetable images using pytesseract.
Detects: day, time slot, room, activity.
"""
from __future__ import annotations
import re
import os
from typing import List, Optional, Tuple

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from backend.config import TESSERACT_CMD, UPLOAD_DIR

if OCR_AVAILABLE:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


# ── Patterns ───────────────────────────────────────────────────────────────────

DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

SLOT_RE = re.compile(
    r'(\d{1,2})[:\.](\d{2})\s*(?:am|pm)?\s*[-–to]+\s*(\d{1,2})[:\.](\d{2})\s*(?:am|pm)?',
    re.I
)
DAY_RE = re.compile(r'\b(' + '|'.join(DAYS) + r')\b', re.I)
ROOM_RE = re.compile(r'\b([A-Ha-h])[\s_]?(\d{1,3})\b')

ACTIVITY_KEYWORDS = [
    'lab', 'lecture', 'tutorial', 'exam', 'workshop', 'seminar',
    'practicals', 'free', 'break', 'maintenance', 'demo', 'library',
    'sports', 'project', 'viva',
]


def _extract_text(image_path: str) -> str:
    """Run OCR on the image and return raw text."""
    if not OCR_AVAILABLE:
        raise RuntimeError(
            "pytesseract / Pillow not installed. "
            "Run: pip install pytesseract pillow"
        )
    img = Image.open(image_path)
    # Improve OCR: convert to grayscale
    img = img.convert('L')
    config = '--oem 3 --psm 6'   # Assume uniform block of text
    return pytesseract.image_to_string(img, config=config)


def _parse_slot(m: re.Match) -> str:
    h1, m1, h2, m2 = m.group(1), m.group(2), m.group(3), m.group(4)
    return f"{int(h1):02d}:{m1}-{int(h2):02d}:{m2}"


def _detect_activity(line: str) -> Optional[str]:
    low = line.lower()
    for kw in ACTIVITY_KEYWORDS:
        if kw in low:
            return kw
    # Return cleaned line as activity if it contains meaningful content
    cleaned = line.strip()
    if len(cleaned) > 3:
        return cleaned[:100]
    return None


def parse_timetable_text(raw_text: str, location: Optional[str] = None) -> List[dict]:
    """
    Parse raw OCR text into structured timetable entries.

    Returns list of dicts: {day, slot, activity, room}
    """
    entries: List[dict] = []
    current_day  = None
    current_slot = None
    current_room = location

    lines = raw_text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect day
        day_m = DAY_RE.search(line)
        if day_m:
            current_day = day_m.group(1).capitalize()

        # Detect slot
        slot_m = SLOT_RE.search(line)
        if slot_m:
            current_slot = _parse_slot(slot_m)

        # Detect room override
        room_m = ROOM_RE.search(line)
        if room_m:
            b = room_m.group(1).upper()
            r = int(room_m.group(2))
            current_room = f"{b}_{r:03d}"

        # Detect activity
        activity = _detect_activity(line)

        if current_day and current_slot and activity:
            entries.append({
                'day':      current_day,
                'slot':     current_slot,
                'activity': activity,
                'room':     current_room or location or 'UNKNOWN',
            })
            # Reset slot after consuming it (each slot is one entry)
            current_slot = None

    # Deduplicate
    seen = set()
    unique_entries = []
    for e in entries:
        key = (e['day'], e['slot'], e['room'])
        if key not in seen:
            seen.add(key)
            unique_entries.append(e)

    return unique_entries


def process_timetable_image(image_path: str, location: str) -> Tuple[str, List[dict]]:
    """
    Full pipeline: image → OCR → parse → structured entries.

    Returns (raw_text, entries_list)
    """
    raw_text = _extract_text(image_path)
    entries  = parse_timetable_text(raw_text, location)
    return raw_text, entries


def mock_timetable_parse(location: str) -> Tuple[str, List[dict]]:
    """
    Fallback mock parser when pytesseract is not available.
    Returns realistic-looking dummy data for testing.
    """
    raw = f"""
TIMETABLE - {location}

Monday
09:00-10:00 Lab Session
10:00-11:00 Lecture
11:00-12:00 Free

Tuesday
09:00-10:00 Workshop
10:00-11:00 Free
14:00-15:00 Practicals

Wednesday
09:00-10:00 Tutorial
11:00-12:00 Seminar
"""
    entries = parse_timetable_text(raw, location)
    return raw, entries
