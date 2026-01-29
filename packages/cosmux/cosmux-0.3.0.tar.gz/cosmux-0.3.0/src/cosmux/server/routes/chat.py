"""Chat API endpoints (non-streaming for testing)"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from cosmux.db.engine import get_session, SessionDep
from cosmux.db.repository import SessionRepository
from cosmux.agent.core import AgentOrchestrator


router = APIRouter()


class ChatRequest(BaseModel):
    """Chat message request"""

    message: str


@router.post("/{session_id}/message")
async def send_message(
    session_id: str,
    request: ChatRequest,
    db: SessionDep = Depends(get_session),
) -> dict:
    """Send a message and get a non-streaming response (for testing)"""
    repo = SessionRepository(db)
    session = repo.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save user message
    repo.add_message(session_id, "user", request.message)

    # Create agent and get response
    agent = AgentOrchestrator(
        workspace_path=session.workspace_path,
        session_id=session_id,
        db=db,
    )

    response_content = ""
    tool_calls = []

    async for event in agent.stream_response(request.message, repo):
        if event["type"] == "text_delta":
            response_content += event["delta"]
        elif event["type"] == "tool_start":
            tool_calls.append({
                "id": event["id"],
                "name": event["name"],
                "input": event["input"],
            })
        elif event["type"] == "tool_end":
            for tc in tool_calls:
                if tc["id"] == event["id"]:
                    tc["output"] = event["output"]
                    tc["success"] = event.get("success", True)

    return {
        "session_id": session_id,
        "message": response_content,
        "tool_calls": tool_calls,
    }
