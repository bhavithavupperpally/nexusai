"""
Embedding generation service.

Supports both lightweight local embeddings (via SentenceTransformer,
`sentence-transformers/all-MiniLM-L6-v2` by default with 384-dimensional output,
running completely offline with zero API cost and zero rate limits) and
Google Gemini embeddings (via the official Google GenAI SDK).

Provides LangChain-compatible ``Embeddings`` implementations for seamless
integration with FAISS.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.embeddings import Embeddings

from app.config import Settings, get_settings
from app.core.exceptions import EmbeddingServiceError, GeminiServiceError, MissingAPIKeyError

logger = logging.getLogger(__name__)


class LocalSentenceTransformerEmbeddings(Embeddings):
    """LangChain-compatible Embeddings adapter for local SentenceTransformer models."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        batch_size: int = 32,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self._model: Any = None

    @property
    def model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("Loading local SentenceTransformer model: %s", self.model_name)
                try:
                    self._model = SentenceTransformer(self.model_name, local_files_only=True)
                except Exception:
                    self._model = SentenceTransformer(self.model_name)
            except Exception as exc:
                logger.exception("Failed to load local embedding model: %s", self.model_name)
                raise EmbeddingServiceError(
                    f"Failed to load local embedding model '{self.model_name}': {exc}"
                ) from exc
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as exc:
            logger.exception("Local embedding generation failed for %d documents", len(texts))
            raise EmbeddingServiceError(f"Local embedding generation failed: {exc}") from exc

    def embed_query(self, text: str) -> list[float]:
        try:
            embedding = self.model.encode(
                text,
                show_progress_bar=False,
                normalize_embeddings=True,
            )
            return embedding.tolist()
        except Exception as exc:
            logger.exception("Local embedding generation failed for query: %s", text[:80])
            raise EmbeddingServiceError(f"Local embedding generation failed: {exc}") from exc


class GeminiEmbeddings(Embeddings):
    """LangChain-compatible Embeddings adapter for Google GenAI."""

    def __init__(
        self,
        client: Any,
        model: str = "gemini-embedding-001",
        output_dimensionality: int = 768,
    ) -> None:
        self._client = client
        self._model = model
        self._output_dimensionality = output_dimensionality

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of text strings in batches."""
        if not texts:
            return []

        from google.genai import types
        from google.genai.errors import APIError

        embeddings: list[list[float]] = []
        batch_size = 50
        config = types.EmbedContentConfig(output_dimensionality=self._output_dimensionality)

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = self._client.models.embed_content(
                    model=self._model,
                    contents=batch,
                    config=config,
                )
                if response.embeddings:
                    for item in response.embeddings:
                        embeddings.append(list(item.values or []))
                else:
                    raise GeminiServiceError("No embeddings returned by Gemini API.")
            except APIError as exc:
                logger.exception("Gemini embed_content failed for batch of %d items", len(batch))
                raise GeminiServiceError(f"Embedding generation failed: {exc}") from exc
            except Exception as exc:
                logger.exception("Unexpected error during Gemini embed_content")
                raise GeminiServiceError(f"Embedding generation failed: {exc}") from exc

        return embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string for semantic similarity search."""
        from google.genai import types
        from google.genai.errors import APIError

        config = types.EmbedContentConfig(output_dimensionality=self._output_dimensionality)
        try:
            response = self._client.models.embed_content(
                model=self._model,
                contents=text,
                config=config,
            )
            if response.embeddings and response.embeddings[0].values:
                return list(response.embeddings[0].values)
            raise GeminiServiceError("No embedding vector returned for query.")
        except APIError as exc:
            logger.exception("Gemini embed_content failed for query: %s", text[:80])
            raise GeminiServiceError(f"Embedding generation failed: {exc}") from exc
        except Exception as exc:
            logger.exception("Unexpected error during Gemini embed_content for query")
            raise GeminiServiceError(f"Embedding generation failed: {exc}") from exc


class EmbeddingService:
    """Produces vector embeddings for text using either local models or Google Gemini."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._embeddings: Embeddings | None = None

    @property
    def provider(self) -> str:
        return self._settings.embedding_provider.lower().strip()

    @property
    def dimension(self) -> int:
        if self.provider == "gemini":
            return 768
        return 384

    @property
    def client(self) -> Embeddings:
        """Lazily instantiate the configured embeddings client."""
        if self._embeddings is None:
            if self.provider == "gemini":
                api_key = self._settings.api_key
                if not api_key:
                    raise MissingAPIKeyError()

                from google import genai

                genai_client = genai.Client(api_key=api_key)
                self._embeddings = GeminiEmbeddings(
                    client=genai_client,
                    model=self._settings.gemini_embedding_model,
                    output_dimensionality=768,
                )
                logger.info(
                    "Initialized GeminiEmbeddings (%s, dim=%d)",
                    self._settings.gemini_embedding_model,
                    768,
                )
            else:
                self._embeddings = LocalSentenceTransformerEmbeddings(
                    model_name=self._settings.local_embedding_model
                )
                logger.info(
                    "Initialized LocalSentenceTransformerEmbeddings (%s, dim=%d)",
                    self._settings.local_embedding_model,
                    self.dimension,
                )
        return self._embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts (used when indexing document chunks)."""
        if not texts:
            return []
        logger.info("Embedding %d text chunks via %s provider", len(texts), self.provider)
        return self.client.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string (used at retrieval time)."""
        return self.client.embed_query(text)
