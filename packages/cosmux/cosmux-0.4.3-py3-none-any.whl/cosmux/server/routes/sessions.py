"""Session management endpoints"""

import json
import os
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from cosmux.db.engine import get_session, SessionDep
from cosmux.db.repository import SessionRepository


def extract_display_content(content: str) -> str:
    """
    Extract human-readable text from message content.

    Assistant messages may be stored as JSON content blocks:
    [{"type": "thinking", "thinking": "...", "signature": "..."}, {"type": "text", "text": "..."}]

    This function extracts only the text content for display to users.

    Args:
        content: Raw message content (may be plain text or JSON)

    Returns:
        Human-readable text content
    """
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            # Extract text from content blocks
            text_parts = []
            for block in parsed:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            if text_parts:
                return "".join(text_parts)
            # No text blocks found, return empty
            return ""
    except (json.JSONDecodeError, TypeError):
        # Plain string content - return as-is
        pass

    return content


router = APIRouter()


# Request/Response models

class SessionCreate(BaseModel):
    """Request to create a session"""

    workspace_path: Optional[str] = None
    name: Optional[str] = None


class SessionUpdate(BaseModel):
    """Request to update a session"""

    name: Optional[str] = None


class SessionResponse(BaseModel):
    """Session response model"""

    id: str
    workspace_path: str
    name: Optional[str]
    created_at: str
    updated_at: str
    message_count: int = 0


class MessageResponse(BaseModel):
    """Message response model"""

    id: int
    role: str
    content: str
    created_at: str


class SessionDetailResponse(SessionResponse):
    """Session with messages"""

    messages: List[MessageResponse] = []


# Endpoints

@router.post("", response_model=SessionResponse)
async def create_session(
    request: SessionCreate,
    db: SessionDep = Depends(get_session),
) -> SessionResponse:
    """Create a new chat session"""
    repo = SessionRepository(db)

    # Use workspace from request or environment
    workspace_path = request.workspace_path or os.environ.get("COSMUX_WORKSPACE", ".")

    session = repo.create_session(
        workspace_path=workspace_path,
        name=request.name,
    )

    return SessionResponse(
        id=session.id,
        workspace_path=session.workspace_path,
        name=session.name,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        message_count=0,
    )


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    workspace_path: Optional[str] = None,
    db: SessionDep = Depends(get_session),
) -> List[SessionResponse]:
    """List all sessions"""
    repo = SessionRepository(db)

    # Use workspace filter from query or environment
    filter_path = workspace_path or os.environ.get("COSMUX_WORKSPACE")

    sessions = repo.list_sessions(workspace_path=filter_path)

    return [
        SessionResponse(
            id=s.id,
            workspace_path=s.workspace_path,
            name=s.name,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
            message_count=len(s.messages),
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: str,
    db: SessionDep = Depends(get_session),
) -> SessionDetailResponse:
    """Get a session with its messages"""
    repo = SessionRepository(db)
    session = repo.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = repo.get_messages(session_id)

    return SessionDetailResponse(
        id=session.id,
        workspace_path=session.workspace_path,
        name=session.name,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        message_count=len(messages),
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role.value,
                content=extract_display_content(m.content),
                created_at=m.created_at.isoformat(),
            )
            for m in messages
        ],
    )


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdate,
    db: SessionDep = Depends(get_session),
) -> SessionResponse:
    """Update a session"""
    repo = SessionRepository(db)

    session = repo.update_session(session_id, name=request.name)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        id=session.id,
        workspace_path=session.workspace_path,
        name=session.name,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        message_count=len(session.messages),
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: SessionDep = Depends(get_session),
) -> dict:
    """Delete a session"""
    repo = SessionRepository(db)

    if not repo.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    return {"status": "deleted", "session_id": session_id}
