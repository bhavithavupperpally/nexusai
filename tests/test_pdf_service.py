"""Unit tests for PDFExtractionService."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.exceptions import UnsupportedFileTypeError
from app.services.pdf_service import PDFExtractionService


def test_extract_pages_returns_text_per_page(sample_pdf_path: Path) -> None:
    service = PDFExtractionService()
    pages = service.extract_pages(sample_pdf_path)

    assert len(pages) == 3
    assert "Retrieval-Augmented Generation" in pages[0]
    assert "Semantic Search" in pages[2]


def test_extract_pages_rejects_non_pdf(tmp_path: Path) -> None:
    fake_file = tmp_path / "not-a-pdf.txt"
    fake_file.write_text("hello world")

    service = PDFExtractionService()
    with pytest.raises(UnsupportedFileTypeError):
        service.extract_pages(fake_file)
