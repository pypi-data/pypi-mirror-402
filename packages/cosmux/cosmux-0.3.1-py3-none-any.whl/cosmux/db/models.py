"""Database models using SQLModel"""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class MessageRole(str, Enum):
    """Message role in conversation"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ToolCallStatus(str, Enum):
    """Status of a tool call"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Session(SQLModel, table=True):
    """Chat session model"""

    __tablename__ = "sessions"

    id: str = Field(primary_key=True)
    workspace_path: str = Field(index=True)
    name: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata_json: Optional[str] = Field(default=None)  # JSON string for flexibility

    # Relationships
    messages: List["Message"] = Relationship(back_populates="session")


class Message(SQLModel, table=True):
    """Message in a chat session"""

    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="sessions.id", index=True)
    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    parent_tool_use_id: Optional[str] = Field(default=None)  # For subagent context

    # Relationships
    session: Session = Relationship(back_populates="messages")
    tool_calls: List["ToolCall"] = Relationship(back_populates="message")


class ToolCall(SQLModel, table=True):
    """Tool call made during a message"""

    __tablename__ = "tool_calls"

    id: Optional[int] = Field(default=None, primary_key=True)
    message_id: int = Field(foreign_key="messages.id", index=True)
    tool_use_id: str = Field(index=True)  # From Claude API
    tool_name: str
    tool_input: str  # JSON string
    tool_output: Optional[str] = Field(default=None)  # JSON string
    status: ToolCallStatus = Field(default=ToolCallStatus.PENDING)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    error: Optional[str] = Field(default=None)

    # Relationships
    message: Message = Relationship(back_populates="tool_calls")
