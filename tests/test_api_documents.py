"""Integration tests for document upload / listing / deletion endpoints.

These tests exercise the extraction, chunking, and vector indexing pipeline
end-to-end. External network calls to embeddings are mocked by default so the
test suite runs offline, fast, and at ₹0 cost.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_documents_empty_by_default() -> None:
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert "documents" in response.json()


def test_upload_rejects_non_pdf(tmp_path: Path) -> None:
    fake_file = tmp_path / "not-a-pdf.txt"
    fake_file.write_text("hello world")

    with fake_file.open("rb") as fh:
        response = client.post(
            "/api/documents", files={"file": ("not-a-pdf.txt", fh, "text/plain")}
        )

    assert response.status_code == 400


def test_upload_indexes_sample_pdf(sample_pdf_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify document upload, text extraction, chunking, and FAISS indexing with mock embeddings."""
    from unittest.mock import MagicMock
    from app.services.embedding_service import EmbeddingService

    mock_client = MagicMock()
    mock_client.embed_documents.side_effect = lambda texts: [[0.05] * 384 for _ in texts]
    mock_client.embed_query.side_effect = lambda text: [0.05] * 384
    monkeypatch.setattr(EmbeddingService, "client", property(lambda self: mock_client))

    with sample_pdf_path.open("rb") as fh:
        response = client.post(
            "/api/documents", files={"file": (sample_pdf_path.name, fh, "application/pdf")}
        )

    assert response.status_code == 201
    body = response.json()
    assert body["document"]["status"] == "indexed"
    assert body["document"]["chunk_count"] > 0
    assert body["document"]["page_count"] == 3


@pytest.mark.skipif(
    not os.environ.get("REAL_GEMINI_API_KEY"),
    reason="Requires a real REAL_GEMINI_API_KEY environment variable to test live external API calls.",
)
def test_upload_indexes_sample_pdf_live(sample_pdf_path: Path) -> None:
    """Intentionally skipped live test, runnable when REAL_GEMINI_API_KEY is supplied."""
    with sample_pdf_path.open("rb") as fh:
        response = client.post(
            "/api/documents", files={"file": (sample_pdf_path.name, fh, "application/pdf")}
        )

    assert response.status_code == 201
    body = response.json()
    assert body["document"]["status"] == "indexed"


def test_failed_ingestion_cleans_up_data(sample_pdf_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that if document ingestion fails, broken disk files and partial store data are cleaned up."""
    from unittest.mock import MagicMock
    from app.config import get_settings
    from app.services.vector_store_service import VectorStoreService

    monkeypatch.setattr(
        VectorStoreService,
        "add_chunks",
        MagicMock(side_effect=RuntimeError("Simulated unexpected vector store error")),
    )

    with sample_pdf_path.open("rb") as fh:
        response = client.post(
            "/api/documents", files={"file": ("test-fail-cleanup.pdf", fh, "application/pdf")}
        )

    assert response.status_code == 500
    upload_dir = get_settings().upload_dir
    uploaded_files = list(upload_dir.glob("*test-fail-cleanup.pdf"))
    assert len(uploaded_files) == 0

