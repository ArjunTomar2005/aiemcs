"""
AIEMCS - NLP Intent Parser
Extracts structured intent from free-text user queries.
Uses regex + keyword matching. Falls back to LangChain if API key is configured.
"""
from __future__ import annotations
import re
from typing import Optional, List, Dict, Any

from backend.services.decision_engine import SearchQuery


# ── Keyword maps ───────────────────────────────────────────────────────────────

EQUIPMENT_KEYWORDS: Dict[str, str] = {
    # Computing
    'computer': 'desktop',   'desktop': 'desktop',   'laptop': 'laptop',
    'pc': 'desktop',         'workstation': 'desktop',
    # Imaging/medical
    'mri': 'imaging',        'ct scan': 'imaging',   'ct': 'imaging',
    'ultrasound': 'imaging', 'x-ray': 'imaging',     'xray': 'imaging',
    # Medical critical
    'ventilator': 'critical', 'defibrillator': 'emergency',
    'ecg': 'cardio',         'dialysis': 'renal',
    'patient monitor': 'monitoring', 'infusion pump': 'drug_admin',
    # Engineering
    'cnc': 'machining',      '3d printer': '3d_print', 'robot': 'robotics',
    'oscilloscope': 'electronics', 'lathe': 'machining', 'welding': 'fabrication',
    'plc': 'automation',     'signal generator': 'electronics',
    # Media
    'camera': 'camera',      'dslr': 'camera',       'drone': 'aerial',
    'mixer': 'audio',        'lighting': 'lighting',  'green screen': 'studio',
    # Science
    'spectrophotometer': 'optical', 'centrifuge': 'separation',
    'autoclave': 'sterilization', 'microscope': 'optical',
    'pcr': 'molecular',      'ph meter': 'chemistry',
    'chromatograph': 'analytical', 'electrophoresis': 'molecular',
    # Agriculture
    'soil sensor': 'sensor', 'weather station': 'sensor',
    'irrigation': 'automation', 'tractor': 'machinery', 'harvester': 'machinery',
    # Kitchen / hotel
    'oven': 'kitchen',       'dishwasher': 'kitchen', 'refrigerator': 'storage',
    'grill': 'kitchen',      'fryer': 'kitchen',      'espresso': 'beverage',
    # Fashion
    'sewing': 'textile',     'embroidery': 'textile', 'knitting': 'textile',
    'heat press': 'printing', 'cutter': 'design',
}

BLOCK_PATTERN    = re.compile(r'\b([A-Ea-eHh])[\s_-]?(\d{1,3})\b')
BLOCK_ONLY       = re.compile(r'\bblock\s*([A-Ea-eHh])\b', re.I)
DAY_PATTERN      = re.compile(
    r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', re.I
)
SLOT_PATTERN     = re.compile(
    r'\b(\d{1,2})[:\.]?(\d{2})?\s*(?:am|pm)?\s*(?:to|-)\s*(\d{1,2})[:\.]?(\d{2})?\s*(?:am|pm)?\b',
    re.I
)
PROC_PATTERN     = re.compile(r'\b(i[3579]|ryzen\s*[3579]|xeon)\b', re.I)
RAM_PATTERN      = re.compile(r'\b(\d+)\s*gb\s*ram\b', re.I)


def _normalize_slot(match: re.Match) -> str:
    h1, m1 = match.group(1), match.group(2) or '00'
    h2, m2 = match.group(3), match.group(4) or '00'
    return f"{int(h1):02d}:{m1}-{int(h2):02d}:{m2}"


def parse_intent(message: str) -> Dict[str, Any]:
    """Parse a natural-language equipment query into structured intent."""
    low = message.lower()

    # Equipment name + category
    equipment_name     = None
    equipment_category = None
    for kw, cat in sorted(EQUIPMENT_KEYWORDS.items(), key=lambda x: -len(x[0])):
        if kw in low:
            equipment_name     = kw
            equipment_category = cat
            break

    # Block location
    block = None
    room  = None
    blk_m = BLOCK_PATTERN.search(message)
    if blk_m:
        block = blk_m.group(1).upper()
        room  = f"{block}_{int(blk_m.group(2)):03d}"
    else:
        blk_only = BLOCK_ONLY.search(message)
        if blk_only:
            block = blk_only.group(1).upper()

    # Day
    day = None
    day_m = DAY_PATTERN.search(low)
    if day_m:
        day = day_m.group(1).capitalize()

    # Time slot
    slot = None
    slot_m = SLOT_PATTERN.search(low)
    if slot_m:
        slot = _normalize_slot(slot_m)

    # Spec keywords
    spec_keywords: List[str] = []
    proc_m = PROC_PATTERN.search(low)
    if proc_m:
        spec_keywords.append(proc_m.group(1).lower())
    ram_m = RAM_PATTERN.search(low)
    if ram_m:
        spec_keywords.append(f"{ram_m.group(1)}gb ram")

    return {
        'equipment_name':     equipment_name,
        'equipment_category': equipment_category,
        'block':              block,
        'room':               room,
        'day':                day,
        'slot':               slot,
        'spec_keywords':      spec_keywords,
        'raw_message':        message,
    }


def build_search_query(message: str) -> SearchQuery:
    """Convert a raw user message into a SearchQuery object."""
    intent = parse_intent(message)
    return SearchQuery(
        equipment_name     = intent['equipment_name'],
        equipment_category = intent['equipment_category'],
        block              = intent['block'],
        day                = intent['day'],
        slot               = intent['slot'],
        spec_keywords      = intent['spec_keywords'],
    )


def format_response(results: list, intent: Dict[str, Any]) -> str:
    """
    Generate a detailed natural-language response showing:
    - Equipment found
    - Location
    - Exactly when it is FREE
    - Suggested nearest slot if requested time is busy
    """
    if not results:
        return (
            "❌ Sorry, I couldn't find any available equipment matching your request.\n"
            "Try a different block, equipment type, or time slot."
        )

    eq_name = intent.get('equipment_name') or 'equipment'
    block   = intent.get('block')
    day     = intent.get('day')
    slot    = intent.get('slot')

    exact        = [r for r in results if r['match_type'] == 'exact']
    same_cat     = [r for r in results if r['match_type'] == 'same_category']
    alternatives = [r for r in results if r['match_type'] == 'alternative']
    nearest_time = [r for r in results if r['match_type'] == 'nearest_time']

    lines = []

    # ── Header ────────────────────────────────────────────────────────────────
    if day and slot:
        lines.append(f"🔍 Searching for: {eq_name.title()}"
                     + (f" in Block {block}" if block else "")
                     + f" on {day} at {slot}\n")
    elif day:
        lines.append(f"🔍 Searching for: {eq_name.title()}"
                     + (f" in Block {block}" if block else "")
                     + f" on {day}\n")
    else:
        lines.append(f"🔍 Searching for: {eq_name.title()}"
                     + (f" in Block {block}" if block else "") + "\n")

    # ── Exact matches ─────────────────────────────────────────────────────────
    if exact:
        lines.append(f"✅ AVAILABLE NOW — {len(exact)} match(es) found:\n")
        for r in exact[:3]:
            lines.append(_format_equipment_entry(r, show_requested_slot=True,
                                                  requested_day=day, requested_slot=slot))
        lines.append("")

    # ── Same category in other blocks ─────────────────────────────────────────
    if same_cat:
        if exact:
            lines.append(f"⚡ Also available in other blocks:\n")
        else:
            lines.append(f"⚠️  Not available in Block {block or '?'} at that time.\n"
                         f"✅ Found in other blocks:\n")
        for r in same_cat[:3]:
            lines.append(_format_equipment_entry(r, show_requested_slot=False,
                                                  requested_day=day, requested_slot=slot))
        lines.append("")

    # ── Alternatives (similar category) ───────────────────────────────────────
    if alternatives and not exact and not same_cat:
        lines.append(f"🔄 Similar equipment available (different category):\n")
        for r in alternatives[:2]:
            lines.append(_format_equipment_entry(r, show_requested_slot=False,
                                                  requested_day=day, requested_slot=slot))
        lines.append("")

    # ── Nearest time fallback ─────────────────────────────────────────────────
    if nearest_time and not exact and not same_cat:
        lines.append(f"🕐 Not available at your requested time. Nearest free slots:\n")
        for r in nearest_time[:3]:
            lines.append(_format_equipment_entry(r, show_requested_slot=False,
                                                  requested_day=day, requested_slot=slot))
        lines.append("")

    # ── If nothing matched at requested time, show when it IS free ────────────
    if not exact and (day or slot) and (same_cat or alternatives or nearest_time):
        lines.append(
            f"💡 Tip: Your requested time ({day or ''} {slot or ''}) may be busy.\n"
            f"   Check the free slots listed above for each equipment."
        )

    return "\n".join(lines).strip()


def _format_equipment_entry(r: dict, show_requested_slot: bool,
                              requested_day: Optional[str],
                              requested_slot: Optional[str]) -> str:
    """Format a single equipment result with full availability details."""
    lines = []

    # Equipment name + specs
    spec = r.get('equipment_model_details') or 'N/A'
    lines.append(f"  📦 {r['equipment_name']} — {spec}")

    # Location + quantity
    lines.append(f"     📍 Location: {r['block_location']}  |  🔢 Qty: {r.get('quantity', 1)}  |  ✅ Status: {r.get('working_status', 'good')}")

    # Free slots info
    free_slots: dict = r.get('free_slots', {})

    if free_slots:
        # If a specific day was requested, show that day's slots first
        if requested_day and requested_day in free_slots:
            day_slots = free_slots[requested_day]
            lines.append(f"     🟢 Free on {requested_day}: {', '.join(day_slots)}")

            # Show 2 more days
            other_days = [d for d in free_slots if d != requested_day][:2]
            for d in other_days:
                s = free_slots[d]
                lines.append(f"     🟢 Free on {d}: {', '.join(s[:3])}" +
                              (f" (+{len(s)-3} more)" if len(s) > 3 else ""))
        else:
            # Show first 3 days with free slots
            shown = 0
            for day_name, slots in free_slots.items():
                if shown >= 3:
                    break
                lines.append(f"     🟢 Free on {day_name}: {', '.join(slots[:3])}" +
                              (f" (+{len(slots)-3} more)" if len(slots) > 3 else ""))
                shown += 1
    else:
        # No utilization data = completely free all week
        lines.append(f"     🟢 Free: All week (no schedule conflicts found)")

    # Suggested nearest slot if available
    if r.get('suggested_day') and r.get('suggested_slot'):
        lines.append(f"     ⭐ Best available: {r['suggested_day']} at {r['suggested_slot']}")

    lines.append("")  # blank line between entries
    return "\n".join(lines)