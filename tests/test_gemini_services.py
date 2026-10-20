"""Unit tests for Gemini-based services (EmbeddingService, ChatService, and VectorStoreService)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from google.genai.errors import APIError

from app.config import Settings
from app.core.exceptions import GeminiServiceError, MissingAPIKeyError
from app.domain.models import RetrievedContext, TextChunk
from app.domain.schemas import StructuredAnswer
from app.services.chat_service import ChatService
from app.services.embedding_service import EmbeddingService, GeminiEmbeddings
from app.services.retrieval_service import RetrievalService
from app.services.vector_store_service import VectorStoreService


class FakeEmbeddingItem:
    def __init__(self, values: list[float]) -> None:
        self.values = values


class FakeEmbedResponse:
    def __init__(self, embeddings: list[FakeEmbeddingItem]) -> None:
        self.embeddings = embeddings


class FakeChunk:
    def __init__(self, text: str) -> None:
        self.text = text


class FakeGenerateResponse:
    def __init__(self, text: str) -> None:
        self.text = text


def test_gemini_embeddings_embed_documents_and_query():
    """Verify GeminiEmbeddings formats batch requests and extracts vectors."""
    mock_client = MagicMock()
    mock_client.models.embed_content.return_value = FakeEmbedResponse(
        [FakeEmbeddingItem([0.1, 0.2, 0.3]), FakeEmbeddingItem([0.4, 0.5, 0.6])]
    )

    embeddings = GeminiEmbeddings(client=mock_client, model="gemini-embedding-001")
    docs = embeddings.embed_documents(["doc 1", "doc 2"])

    assert len(docs) == 2
    assert docs[0] == [0.1, 0.2, 0.3]
    assert docs[1] == [0.4, 0.5, 0.6]

    # Query embedding
    mock_client.models.embed_content.return_value = FakeEmbedResponse(
        [FakeEmbeddingItem([0.7, 0.8, 0.9])]
    )
    query_vec = embeddings.embed_query("search query")
    assert query_vec == [0.7, 0.8, 0.9]


def test_gemini_embeddings_handles_empty_list():
    mock_client = MagicMock()
    embeddings = GeminiEmbeddings(client=mock_client)
    assert embeddings.embed_documents([]) == []


def test_gemini_embeddings_raises_gemini_service_error_on_api_failure():
    mock_client = MagicMock()
    mock_client.models.embed_content.side_effect = APIError(500, {"error": "Service unavailable"})

    embeddings = GeminiEmbeddings(client=mock_client)
    with pytest.raises(GeminiServiceError) as exc_info:
        embeddings.embed_query("fail query")
    assert "Embedding generation failed" in str(exc_info.value)


def test_embedding_service_requires_api_key_for_gemini():
    settings = Settings(embedding_provider="gemini", gemini_api_key="", openai_api_key="")
    service = EmbeddingService(settings=settings)
    with pytest.raises(MissingAPIKeyError):
        _ = service.client


def test_embedding_service_local_provider():
    settings = Settings(embedding_provider="local", gemini_api_key="")
    service = EmbeddingService(settings=settings)
    assert service.provider == "local"
    assert service.dimension == 384
    query_vec = service.embed_query("test query")
    assert len(query_vec) == 384


def test_local_embeddings_embed_documents():
    from app.services.embedding_service import LocalSentenceTransformerEmbeddings

    embedder = LocalSentenceTransformerEmbeddings()
    docs = embedder.embed_documents(["First chunk", "Second chunk"])
    assert len(docs) == 2
    assert len(docs[0]) == 384
    assert len(docs[1]) == 384



def test_chat_service_stream_answer():
    """Verify ChatService streams tokens from generate_content_stream."""
    mock_client = MagicMock()
    mock_client.models.generate_content_stream.return_value = iter(
        [FakeChunk("Retrieval "), FakeChunk("Augmented "), FakeChunk("Generation.")]
    )

    service = ChatService(settings=Settings(gemini_api_key="fake-key"))
    service._client = mock_client

    chunk = TextChunk(
        chunk_id="c1",
        document_id="d1",
        document_name="guide.pdf",
        page_number=1,
        content="RAG combines retrieval with language models.",
        chunk_index=0,
    )
    contexts = [RetrievedContext(chunk=chunk, score=0.9)]

    tokens = list(service.stream_answer("What is RAG?", contexts))
    assert tokens == ["Retrieval ", "Augmented ", "Generation."]
    mock_client.models.generate_content_stream.assert_called_once()


def test_chat_service_generate_structured_answer():
    """Verify ChatService parses structured JSON into StructuredAnswer schema."""
    expected_payload = {
        "answer_found": True,
        "answer": "RAG enhances generation with relevant retrieved excerpts.",
        "key_points": ["Combines search and LLM", "Grounded answers"],
        "sources": [],
        "confidence": 0.92,
    }
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = FakeGenerateResponse(
        json.dumps(expected_payload)
    )

    service = ChatService(settings=Settings(gemini_api_key="fake-key"))
    service._client = mock_client

    chunk = TextChunk(
        chunk_id="c1",
        document_id="d1",
        document_name="guide.pdf",
        page_number=1,
        content="RAG enhances generation with relevant retrieved excerpts.",
        chunk_index=0,
    )
    contexts = [RetrievedContext(chunk=chunk, score=0.9)]

    answer = service.generate_structured_answer("How does RAG work?", contexts)
    assert isinstance(answer, StructuredAnswer)
    assert answer.answer_found is True
    assert answer.confidence == 0.92
    assert len(answer.key_points) == 2
    # Verify fallback sources populated from context
    assert len(answer.sources) == 1
    assert answer.sources[0].document_name == "guide.pdf"
    assert answer.sources[0].page_number == 1


def test_chat_service_raises_on_api_error():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = APIError(403, {"error": "Quota exceeded"})

    service = ChatService(settings=Settings(gemini_api_key="fake-key"))
    service._client = mock_client

    with pytest.raises(GeminiServiceError):
        service.generate_structured_answer("query", [])


def test_vector_store_reset_index(tmp_path):
    """Verify VectorStoreService reset_index clears stored files."""
    settings = Settings(
        vector_store_dir=tmp_path / "vs",
        gemini_api_key="fake-key",
    )
    index_file = settings.vector_store_dir / "index.faiss"
    index_file.parent.mkdir(parents=True, exist_ok=True)
    index_file.write_text("dummy index content")

    assert index_file.exists()
    vs = VectorStoreService(settings=settings)
    vs.reset_index()

    assert not index_file.exists()
