"""Unit tests for ChunkingService."""

from __future__ import annotations

from app.services.chunking_service import ChunkingService


def test_chunk_pages_produces_non_empty_chunks() -> None:
    service = ChunkingService(chunk_size=50, chunk_overlap=10)
    pages = [
        "This is the first page. " * 10,
        "This is the second page. " * 10,
    ]

    chunks = service.chunk_pages(pages, document_id="doc-1", document_name="test.pdf")

    assert len(chunks) > 0
    assert all(chunk.content.strip() for chunk in chunks)
    assert all(chunk.document_id == "doc-1" for chunk in chunks)
    # Page numbers should be 1-indexed and reflect source page.
    assert chunks[0].page_number == 1
    assert chunks[-1].page_number == 2


def test_chunk_pages_skips_blank_pages() -> None:
    service = ChunkingService(chunk_size=100, chunk_overlap=10)
    pages = ["", "   ", "Real content goes here."]

    chunks = service.chunk_pages(pages, document_id="doc-2", document_name="test.pdf")

    assert len(chunks) == 1
    assert chunks[0].page_number == 3


def test_chunk_indices_are_sequential() -> None:
    service = ChunkingService(chunk_size=20, chunk_overlap=5)
    pages = ["A" * 100]

    chunks = service.chunk_pages(pages, document_id="doc-3", document_name="test.pdf")

    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))
