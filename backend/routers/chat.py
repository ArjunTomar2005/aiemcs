"""
AIEMCS - Chatbot Router (updated with history support)
POST /chat
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config import get_db, DATABASE_URL
from backend.schemas.schemas import ChatResponse, EquipmentResult
from backend.services.langchain_agent import process_chat

router = APIRouter(prefix="/chat", tags=["Chatbot"])


class HistoryMessage(BaseModel):
    role: str      # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message:    str
    session_id: Optional[str] = None
    history:    Optional[List[HistoryMessage]] = []


@router.post("", response_model=ChatResponse, summary="Equipment availability chatbot")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Accept a natural-language equipment query with conversation history.
    Returns intelligent results with context from previous messages.
    """
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Convert history to plain dicts for the agent
    history = [{"role": h.role, "content": h.content} for h in (payload.history or [])]

    response = process_chat(
        message = payload.message,
        db      = db,
        db_url  = DATABASE_URL,
        history = history,
    )

    results = [
        EquipmentResult(**{k: v for k, v in r.items() if k in EquipmentResult.model_fields})
        for r in response.get("results", [])
    ]

    return ChatResponse(
        answer  = response["answer"],
        results = results,
        intent  = response.get("intent"),
    )