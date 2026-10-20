"""
Chunking service.

Splits extracted page text into overlapping chunks sized for embedding and
retrieval. Uses LangChain's ``RecursiveCharacterTextSplitter``, which tries
a sequence of separators (paragraphs, then sentences, then words) to keep
chunks semantically coherent rather than cutting mid-sentence.
"""

from __future__ import annotations

import logging
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.domain.models import TextChunk

logger = logging.getLogger(__name__)


class ChunkingService:
    """Splits document pages into retrieval-ready text chunks."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def chunk_pages(
        self, pages: list[str], document_id: str, document_name: str
    ) -> list[TextChunk]:
        """Convert a list of page texts into a flat list of :class:`TextChunk`."""
        chunks: list[TextChunk] = []
        chunk_index = 0

        for page_number, page_text in enumerate(pages, start=1):
            if not page_text.strip():
                continue
            for piece in self._splitter.split_text(page_text):
                if not piece.strip():
                    continue
                chunks.append(
                    TextChunk(
                        chunk_id=str(uuid.uuid4()),
                        document_id=document_id,
                        document_name=document_name,
                        page_number=page_number,
                        content=piece.strip(),
                        chunk_index=chunk_index,
                    )
                )
                chunk_index += 1

        logger.info(
            "Chunked '%s' into %d chunks across %d pages", document_name, len(chunks), len(pages)
        )
        return chunks
