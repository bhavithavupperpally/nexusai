"""
Domain entities.

These dataclasses represent the core business objects of the application,
independent of how they are persisted (SQLAlchemy) or transmitted over the
wire (Pydantic schemas in ``app.domain.schemas``). Keeping them separate is
a Clean Architecture principle: the domain should not depend on
infrastructure or delivery-mechanism details.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """Lifecycle states of an uploaded document."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class MessageRole(str, Enum):
    """Role of a message within a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass(slots=True)
class TextChunk:
    """A single chunk of extracted text, ready for embedding."""

    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    content: str
    chunk_index: int


@dataclass(slots=True)
class RetrievedContext:
    """A chunk retrieved from the vector store along with its relevance score."""

    chunk: TextChunk
    score: float


@dataclass(slots=True)
class Document:
    """An uploaded PDF document tracked by the system."""

    id: str
    filename: str
    stored_path: str
    status: DocumentStatus
    page_count: int = 0
    chunk_count: int = 0
    size_bytes: int = 0
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
    error_message: str | None = None


@dataclass(slots=True)
class ChatMessage:
    """A single message exchanged within a conversation."""

    id: str
    conversation_id: str
    role: MessageRole
    content: str
    sources: list[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class Conversation:
    """A conversation thread grouping related chat messages."""

    id: str
    title: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    messages: list[ChatMessage] = field(default_factory=list)
