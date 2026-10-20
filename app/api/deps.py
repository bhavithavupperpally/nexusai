"""
FastAPI dependency providers.

Centralizes construction of service-layer objects so route handlers stay
declarative and testable (dependencies can be overridden in tests via
``app.dependency_overrides``).
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.db import get_db
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService
from app.services.embedding_service import EmbeddingService
from app.services.memory_service import MemoryService
from app.services.retrieval_service import RetrievalService
from app.services.vector_store_service import VectorStoreService

# Embeddings and the vector store are process-wide singletons: the FAISS
# index is memory-mapped from disk and safe to share across requests within
# a single worker process.
_embedding_service = EmbeddingService()
_vector_store_service = VectorStoreService(embedding_service=_embedding_service)
_retrieval_service = RetrievalService(vector_store_service=_vector_store_service)
_chat_service = ChatService(retrieval_service=_retrieval_service)


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


def get_document_service(db: Session = Depends(get_db_session)) -> DocumentService:
    return DocumentService(db=db, vector_store_service=_vector_store_service)


def get_memory_service(db: Session = Depends(get_db_session)) -> MemoryService:
    return MemoryService(db=db)


def get_chat_service() -> ChatService:
    return _chat_service


def get_retrieval_service() -> RetrievalService:
    return _retrieval_service


def get_vector_store_service() -> VectorStoreService:
    return _vector_store_service
