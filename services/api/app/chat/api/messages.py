"""Messages streaming API endpoint (Part B2.3).
Returns SSE event stream for conversation turn.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.api.app.chat.router.intent_router import intent_router
from services.api.app.chat.runtime.loop import AgentRuntimeLoop
from services.api.app.core.auth import AuthContext, get_auth_context

router = APIRouter(prefix="/conversations", tags=["messages"])

class SendMessageRequest(BaseModel):
    content: str
    agent_key: Optional[str] = None

runtime_loop = AgentRuntimeLoop()

@router.post("/{id}/messages")
async def send_message(
    id: UUID,
    req: SendMessageRequest,
    auth: AuthContext = Depends(get_auth_context),
):
    # Enforce read-only constraint for viewer role
    if auth.role == "viewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewer role is read-only and cannot send messages or run scenarios.",
        )

    # 1. Intent Routing
    route = intent_router.route(req.content, forced_agent=req.agent_key)

    # Check destructive refusal
    if route.is_destructive:
        async def refusal_stream():
            yield "event: token\ndata: {\"delta\": \"I cannot execute destructive data deletion requests per safety policy.\"}\n\n"
            yield "event: done\ndata: {\"status\": \"failed\"}\n\n"
        return StreamingResponse(refusal_stream(), media_type="text/event-stream")

    # 2. Execute turn via AgentRuntimeLoop and stream SSE events
    stream_generator = runtime_loop.execute_turn(
        conversation_id=id,
        user_message=req.content,
        auth=auth,
        agent_key=route.agent_key,
    )

    return StreamingResponse(
        stream_generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
