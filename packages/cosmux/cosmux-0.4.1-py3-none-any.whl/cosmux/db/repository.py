"""Repository pattern for database operations"""

import json
import uuid
from datetime import datetime
from typing import Optional, List

from sqlmodel import Session, select

from cosmux.db.models import (
    Session as ChatSession,
    Message,
    ToolCall,
    MessageRole,
    ToolCallStatus,
)


class SessionRepository:
    """Repository for session and message operations"""

    def __init__(self, db: Session):
        self.db = db

    # Session operations

    def create_session(self, workspace_path: str, name: Optional[str] = None) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(
            id=str(uuid.uuid4()),
            workspace_path=workspace_path,
            name=name,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a session by ID"""
        return self.db.get(ChatSession, session_id)

    def list_sessions(self, workspace_path: Optional[str] = None) -> List[ChatSession]:
        """List all sessions, optionally filtered by workspace"""
        statement = select(ChatSession).order_by(ChatSession.updated_at.desc())
        if workspace_path:
            statement = statement.where(ChatSession.workspace_path == workspace_path)
        return list(self.db.exec(statement).all())

    def update_session(self, session_id: str, **kwargs) -> Optional[ChatSession]:
        """Update a session"""
        session = self.get_session(session_id)
        if not session:
            return None

        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.updated_at = datetime.utcnow()
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        session = self.get_session(session_id)
        if not session:
            return False

        # Delete all messages (cascades to tool_calls)
        for message in session.messages:
            for tool_call in message.tool_calls:
                self.db.delete(tool_call)
            self.db.delete(message)

        self.db.delete(session)
        self.db.commit()
        return True

    # Message operations

    def add_message(
        self,
        session_id: str,
        role: str | MessageRole,
        content: str | list,
        parent_tool_use_id: Optional[str] = None,
    ) -> Message:
        """
        Add a message to a session.

        Args:
            session_id: The session ID
            role: Message role (user, assistant, system)
            content: Message content - can be:
                - A plain string (for simple messages)
                - A list of content blocks (for assistant messages with thinking/tool_use)
            parent_tool_use_id: Optional parent tool use ID for subagent context
        """
        if isinstance(role, str):
            role = MessageRole(role)

        # Store content as JSON if it's a list of content blocks
        if isinstance(content, list):
            content_str = json.dumps(content)
        else:
            content_str = content

        message = Message(
            session_id=session_id,
            role=role,
            content=content_str,
            created_at=datetime.utcnow(),
            parent_tool_use_id=parent_tool_use_id,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        # Update session's updated_at
        session = self.get_session(session_id)
        if session:
            session.updated_at = datetime.utcnow()
            self.db.add(session)
            self.db.commit()

        return message

    def get_messages(self, session_id: str) -> List[Message]:
        """Get all messages for a session"""
        statement = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
        )
        return list(self.db.exec(statement).all())

    def get_message_history(self, session_id: str) -> List[dict]:
        """
        Get message history for Claude API.

        Handles both plain string content and JSON content blocks.
        NOTE: Thinking/tool_use filtering is handled in AgentOrchestrator._convert_messages_for_api()
        """
        messages = self.get_messages(session_id)
        history = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                continue  # System messages are handled separately

            # Try to parse content as JSON (for content blocks)
            # This applies to both assistant messages (thinking/text blocks)
            # and potentially user messages (tool_result blocks - shouldn't exist but handle for safety)
            content = msg.content
            try:
                parsed = json.loads(content)
                if isinstance(parsed, list):
                    content = parsed
            except (json.JSONDecodeError, TypeError):
                # Plain string content - use as-is
                pass

            history.append({
                "role": msg.role.value,
                "content": content,
            })

        return history

    def clear_messages(self, session_id: str) -> int:
        """
        Clear all messages for a session (used during context compaction).

        Args:
            session_id: The session ID

        Returns:
            Number of messages deleted
        """
        messages = self.get_messages(session_id)
        count = len(messages)

        for message in messages:
            # Delete associated tool calls first
            for tool_call in message.tool_calls:
                self.db.delete(tool_call)
            self.db.delete(message)

        self.db.commit()
        return count

    # Tool call operations

    def add_tool_call(
        self,
        message_id: int,
        tool_use_id: str,
        tool_name: str,
        tool_input: dict,
    ) -> ToolCall:
        """Add a tool call to a message"""
        tool_call = ToolCall(
            message_id=message_id,
            tool_use_id=tool_use_id,
            tool_name=tool_name,
            tool_input=json.dumps(tool_input),
            status=ToolCallStatus.PENDING,
        )
        self.db.add(tool_call)
        self.db.commit()
        self.db.refresh(tool_call)
        return tool_call

    def update_tool_call(
        self,
        tool_use_id: str,
        status: ToolCallStatus,
        output: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> Optional[ToolCall]:
        """Update a tool call status and output"""
        statement = select(ToolCall).where(ToolCall.tool_use_id == tool_use_id)
        tool_call = self.db.exec(statement).first()

        if not tool_call:
            return None

        tool_call.status = status
        if output is not None:
            tool_call.tool_output = json.dumps(output)
        if error is not None:
            tool_call.error = error

        if status == ToolCallStatus.RUNNING:
            tool_call.started_at = datetime.utcnow()
        elif status in (ToolCallStatus.COMPLETED, ToolCallStatus.FAILED):
            tool_call.completed_at = datetime.utcnow()

        self.db.add(tool_call)
        self.db.commit()
        self.db.refresh(tool_call)
        return tool_call
