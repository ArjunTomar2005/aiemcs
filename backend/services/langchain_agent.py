"""
AIEMCS - LangChain AI Agent with Conversation Memory
Uses Google Gemini 2.5 Flash.
- Detects equipment intent before searching DB
- Handles greetings and non-equipment messages gracefully
- Maintains conversation history for context-aware responses
"""
from __future__ import annotations
import os
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session

from backend.config import OPENAI_API_KEY, GEMINI_API_KEY, USE_AI
from backend.services.nlp_parser import parse_intent, build_search_query, format_response
from backend.services.decision_engine import search_equipment


SYSTEM_PROMPT = """You are AIEMCS — an AI assistant for an institutional equipment management system.

Your job is to help users find available equipment across university blocks (A, B, C, D, E) and hospital block (H).

IMPORTANT: You have access to the conversation history. Use it to:
- Remember what equipment was discussed earlier
- Understand follow-up questions like "what about Saturday?" or "are there i7 ones?"
- Connect context across messages
- Answer questions like "is the institute closed on Saturday?" based on schedule data

When a user asks about equipment:
1. Read the conversation history to understand context
2. Understand what equipment they need
3. Note any location, day, and time mentioned
4. Based on the search results, give a clear helpful answer

Always mention:
- Equipment name and specifications
- Location (block and room number)
- When it is FREE (available time slots by day)
- If their requested time is busy, suggest the nearest free slot
- How many units are available

Be conversational, friendly, and remember previous messages in the chat.
Never make up equipment not in the search results.
"""

NO_EQUIPMENT_PROMPT = """You are AIEMCS — an AI assistant for institutional equipment management.

The user has sent a message that does NOT contain any equipment request.

Respond naturally and conversationally to what they said.
Then end with a simple, friendly question asking what equipment they need.

Rules:
- Keep it SHORT — 1 to 2 sentences max
- Do NOT list specifications like i7, 16GB RAM, etc.
- Do NOT give a long list of instructions
- Just ask naturally: "What equipment are you looking for?" or "Which equipment do you need today?"
- Vary the ending question each time so it doesn't feel repetitive
"""


# ── Greeting detection ─────────────────────────────────────────────────────────

GREETINGS = {
    'hi', 'hello', 'hey', 'hii', 'helo', 'heyy', 'heya', 'howdy',
    'sup', 'greetings', 'help', 'good morning', 'good afternoon',
    'good evening', 'good night', 'what\'s up', 'whats up', 'yo'
}

def _is_greeting(message: str) -> bool:
    """Return True if message is just a greeting with no equipment intent."""
    clean = message.lower().strip().rstrip('!.,?')
    return clean in GREETINGS


def _has_equipment_intent(intent_dict: dict) -> bool:
    """Return True if the message contains any equipment-related intent."""
    return bool(
        intent_dict.get('equipment_name') or
        intent_dict.get('equipment_category') or
        intent_dict.get('spec_keywords')
    )


# ── LLM initialization ─────────────────────────────────────────────────────────

def _build_gemini_llm():
    """Initialize Google Gemini 2.5 Flash LLM."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.3,
        )
        print("✅ Gemini AI agent ready (gemini-2.5-flash)")
        return llm
    except ImportError:
        print("[Gemini] Missing package. Run: pip install langchain-google-genai")
        return None
    except Exception as e:
        print(f"[Gemini] Failed to initialize: {e}")
        return None


def _build_openai_llm():
    """Initialize OpenAI LLM as fallback."""
    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=OPENAI_API_KEY)
        print("✅ OpenAI agent ready (gpt-3.5-turbo)")
        return llm
    except Exception as e:
        print(f"[OpenAI] Failed: {e}")
        return None


_llm_cache: Optional[Any] = None


def _get_llm():
    """Lazily initialize and cache the best available LLM."""
    global _llm_cache
    if _llm_cache is not None:
        return _llm_cache
    if GEMINI_API_KEY:
        _llm_cache = _build_gemini_llm()
        if _llm_cache:
            return _llm_cache
    if OPENAI_API_KEY:
        _llm_cache = _build_openai_llm()
        if _llm_cache:
            return _llm_cache
    print("[AI] No working AI model. Using rule-based responses.")
    return None


# ── Result formatter ───────────────────────────────────────────────────────────

def _format_results_for_llm(results: list) -> str:
    """Format DB search results into readable context for the LLM."""
    if not results:
        return "No equipment found in the database matching this query."

    text = "EQUIPMENT FOUND IN DATABASE:\n"
    for i, r in enumerate(results[:5], 1):
        text += f"\n--- Result {i} ---"
        text += f"\nName: {r['equipment_name']}"
        text += f"\nSpecs: {r.get('equipment_model_details') or 'N/A'}"
        text += f"\nLocation: {r.get('block_location') or 'N/A'}"
        text += f"\nQuantity available: {r.get('quantity', 1)}"
        text += f"\nWorking status: {r.get('working_status', 'good')}"
        text += f"\nMatch type: {r.get('match_type', 'N/A')}"

        free_slots: dict = r.get('free_slots', {})
        if free_slots:
            text += "\nFree time slots:"
            for day, slots in list(free_slots.items())[:6]:
                text += f"\n  {day}: {', '.join(slots)}"
        else:
            text += "\nFree time slots: Available all week (no schedule conflicts)"

        if r.get('suggested_day'):
            text += f"\nBest available slot: {r['suggested_day']} at {r['suggested_slot']}"

    return text


# ── LLM callers ────────────────────────────────────────────────────────────────

def _ask_llm_equipment(llm, user_message: str, results: list,
                       history: Optional[List[Dict]] = None) -> Optional[str]:
    """Send equipment query + DB results + history to Gemini."""
    try:
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

        results_context = _format_results_for_llm(results)
        messages = [SystemMessage(content=SYSTEM_PROMPT)]

        if history:
            for h in history[:-1]:
                if h['role'] == 'user':
                    messages.append(HumanMessage(content=h['content']))
                elif h['role'] == 'assistant':
                    messages.append(AIMessage(content=h['content']))

        messages.append(HumanMessage(content=(
            f"FRESH DATABASE SEARCH RESULTS:\n{results_context}\n\n"
            f"CURRENT USER MESSAGE: {user_message}\n\n"
            f"Using the conversation history and search results, give a helpful context-aware response."
        )))

        response = llm.invoke(messages)
        return response.content

    except Exception as e:
        err = str(e)
        if "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
            print("[LLM] Quota exceeded. Falling back to rule-based.")
        else:
            print(f"[LLM] Generation error: {err[:200]}")
        return None


def _ask_llm_non_equipment(llm, user_message: str,
                            history: Optional[List[Dict]] = None) -> Optional[str]:
    """Handle non-equipment messages — respond naturally but ask for equipment."""
    try:
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

        messages = [SystemMessage(content=NO_EQUIPMENT_PROMPT)]

        if history:
            for h in history[:-1]:
                if h['role'] == 'user':
                    messages.append(HumanMessage(content=h['content']))
                elif h['role'] == 'assistant':
                    messages.append(AIMessage(content=h['content']))

        messages.append(HumanMessage(content=user_message))

        response = llm.invoke(messages)
        return response.content

    except Exception as e:
        print(f"[LLM] Non-equipment error: {str(e)[:200]}")
        return None


# ── Static fallback response ───────────────────────────────────────────────────

FALLBACK_NO_EQUIPMENT = (
    "👋 I'm AIEMCS, your equipment assistant!\n\n"
    "Please tell me which equipment you are looking for. You can specify:\n"
    "• Equipment type — laptop, MRI, CNC, microscope, camera, sewing machine…\n"
    "• Block & room — Block E, Block H, A_101…\n"
    "• Day & time — Monday 10:00-11:00, Friday afternoon…\n"
    "• Specifications — i7 processor, 16GB RAM…\n\n"
    "🔍 Which equipment do you need?"
)


# ── Main entry point ───────────────────────────────────────────────────────────

def process_chat(message: str, db: Session,
                 db_url: str = "",
                 history: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Main chat processing with conversation memory.

    Flow:
    1. Parse intent from message
    2. If no equipment intent → respond conversationally + ask for equipment
    3. If equipment intent → search DB → AI natural language response
    4. Rule-based fallback if AI unavailable
    """
    intent_dict = parse_intent(message)
    has_equipment = _has_equipment_intent(intent_dict)

    # ── No equipment intent — don't search DB ─────────────────────────────────
    if not has_equipment:
        if USE_AI:
            llm = _get_llm()
            if llm:
                ai_answer = _ask_llm_non_equipment(llm, message, history)
                if ai_answer:
                    return {
                        "answer":  ai_answer,
                        "results": [],
                        "intent":  "no_equipment",
                    }
        # Rule-based fallback
        return {
            "answer":  FALLBACK_NO_EQUIPMENT,
            "results": [],
            "intent":  "no_equipment",
        }

    # ── Equipment intent — search DB and respond ───────────────────────────────
    sq      = build_search_query(message)
    results = search_equipment(db, sq)

    if USE_AI:
        llm = _get_llm()
        if llm:
            ai_answer = _ask_llm_equipment(llm, message, results, history)
            if ai_answer:
                return {
                    "answer":  ai_answer,
                    "results": results,
                    "intent":  "gemini_ai" if GEMINI_API_KEY else "openai_ai",
                }

    # Rule-based fallback
    answer = format_response(results, intent_dict)
    return {
        "answer":  answer,
        "results": results,
        "intent":  "rule_based",
    }