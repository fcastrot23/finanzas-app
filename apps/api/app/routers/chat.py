"""Chat router — conversational AI agent (tool-use → core Python)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.models.schemas import ChatRequest, ChatResponse
from app.security.auth import get_current_uid, require_household_member

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    uid: str = Depends(get_current_uid),
) -> ChatResponse:
    """Conversational agent: narrates, simulates, explains — never computes money. API-1.15."""
    require_household_member(uid, body.household_id)
    from app.ai.agent import run_agent

    return await run_agent(body, uid)
