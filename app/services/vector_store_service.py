"""
Vector database service.

Wraps a LangChain FAISS vector store to provide persistent, on-disk
similarity search over document chunk embeddings. FAISS (Facebook AI
Similarity Search) performs efficient approximate/exact nearest-neighbour
search over dense vectors, which is the core "retrieval" step of RAG.

The index is persisted to ``settings.vector_store_dir`` so it survives
application restarts, and is lazily loaded on first use.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from langchain_community.docstore.document import Document as LCDocument
from langchain_community.vectorstores import FAISS

from app.config import Settings, get_settings
from app.core.constants import FAISS_INDEX_FILENAME
from app.core.exceptions import VectorStoreNotReadyError
from app.domain.models import RetrievedContext, TextChunk
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Manages a persistent FAISS index of document chunk embeddings."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._embedding_service = embedding_service or EmbeddingService(self._settings)
        self._store: FAISS | None = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @property
    def _index_path(self) -> Path:
        return self._settings.vector_store_dir

    def _index_exists(self) -> bool:
        return (self._index_path / FAISS_INDEX_FILENAME).exists()

    def _load(self) -> FAISS | None:
        if self._store is not None:
            return self._store
        if not self._index_exists():
            return None
        logger.info("Loading FAISS index from %s", self._index_path)
        try:
            self._store = FAISS.load_local(
                str(self._index_path),
                self._embedding_service.client,
                allow_dangerous_deserialization=True,
            )
            expected_dim = getattr(self._embedding_service, "dimension", None)
            if expected_dim is not None and hasattr(self._store, "index") and self._store.index.d != expected_dim:
                logger.warning(
                    "FAISS index dimension (%d) does not match embedding dimension (%d). Safely resetting index.",
                    self._store.index.d,
                    expected_dim,
                )
                self._clear_index()
                return None
            return self._store
        except Exception as exc:
            logger.warning(
                "Failed to load existing FAISS index (likely incompatible embedding dimensions or corrupt store): %s. "
                "Safely resetting index.",
                exc,
            )
            self._clear_index()
            return None

    @staticmethod
    def _chunk_to_document(chunk: TextChunk) -> LCDocument:
        return LCDocument(
            page_content=chunk.content,
            metadata={
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "document_name": chunk.document_name,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
            },
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_chunks(self, chunks: list[TextChunk]) -> int:
        """Embed and add chunks to the index, creating it if necessary."""
        if not chunks:
            return 0

        documents = [self._chunk_to_document(chunk) for chunk in chunks]

        with self._lock:
            existing = self._load()
            if existing is None:
                logger.info("Creating new FAISS index with %d chunks", len(documents))
                self._store = FAISS.from_documents(documents, self._embedding_service.client)
            else:
                logger.info("Adding %d chunks to existing FAISS index", len(documents))
                try:
                    existing.add_documents(documents)
                    self._store = existing
                except Exception as exc:
                    logger.warning(
                        "Failed to add documents to existing index (dimension mismatch or corruption): %s. Recreating index.",
                        exc,
                    )
                    self._clear_index()
                    self._store = FAISS.from_documents(documents, self._embedding_service.client)

            self._index_path.mkdir(parents=True, exist_ok=True)
            self._store.save_local(str(self._index_path))

        return len(documents)

    def reset_index(self) -> None:
        """Safely clear and reset the vector store index."""
        with self._lock:
            self._clear_index()

    def similarity_search(
        self,
        query: str,
        top_k: int = 4,
        document_ids: list[str] | None = None,
    ) -> list[RetrievedContext]:
        """Perform semantic search and return the top-k most relevant chunks."""
        store = self._load()
        if store is None:
            raise VectorStoreNotReadyError()

        # Over-fetch when filtering by document id, since FAISS similarity
        # search does not natively support metadata pre-filtering.
        fetch_k = top_k * 5 if document_ids else top_k
        results = store.similarity_search_with_relevance_scores(query, k=fetch_k)

        contexts: list[RetrievedContext] = []
        for doc, score in results:
            metadata = doc.metadata
            if document_ids and metadata.get("document_id") not in document_ids:
                continue
            chunk = TextChunk(
                chunk_id=metadata.get("chunk_id", ""),
                document_id=metadata.get("document_id", ""),
                document_name=metadata.get("document_name", "Unknown"),
                page_number=metadata.get("page_number", 0),
                content=doc.page_content,
                chunk_index=metadata.get("chunk_index", 0),
            )
            contexts.append(RetrievedContext(chunk=chunk, score=float(score)))
            if len(contexts) >= top_k:
                break

        logger.info("Retrieved %d chunks for query (top_k=%d)", len(contexts), top_k)
        return contexts

    def is_ready(self) -> bool:
        return self._load() is not None

    def delete_document(self, document_id: str) -> None:
        """Rebuild the index excluding all chunks belonging to a document.

        FAISS does not support efficient in-place deletion by metadata, so we
        reconstruct the index from the remaining in-memory docstore entries.
        This is acceptable for the moderate document volumes typical of a
        single-tenant / small-team deployment.
        """
        store = self._load()
        if store is None:
            return

        with self._lock:
            docstore_dict = store.docstore._dict  # type: ignore[attr-defined]
            remaining = [
                doc
                for doc in docstore_dict.values()
                if doc.metadata.get("document_id") != document_id
            ]
            if not remaining:
                self._clear_index()
                return

            self._store = FAISS.from_documents(remaining, self._embedding_service.client)
            self._store.save_local(str(self._index_path))
            logger.info("Rebuilt FAISS index after deleting document %s", document_id)

    def _clear_index(self) -> None:
        import shutil

        if self._index_path.exists():
            shutil.rmtree(self._index_path)
        self._index_path.mkdir(parents=True, exist_ok=True)
        self._store = None
        logger.info("Cleared FAISS index (no documents remaining)")
