"""
Chat / RAG orchestration service.

Coordinates retrieval and generation to answer questions over uploaded PDFs
using Google Gemini (via the official Google GenAI SDK).

Two generation modes are supported:
* :meth:`ChatService.stream_answer` - token-by-token streaming, used by the
  ``/api/chat/stream`` SSE endpoint for a responsive chat UI.
* :meth:`ChatService.generate_structured_answer` - a single structured-output
  call constrained to the :class:`StructuredAnswer` Pydantic schema using
  Gemini's native JSON schema enforcement.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

from google import genai
from google.genai import types
from google.genai.errors import APIError
from langchain_core.prompts import PromptTemplate

from app.config import Settings, get_settings
from app.core.constants import DEFAULT_SYSTEM_PROMPT, STRUCTURED_SYSTEM_PROMPT
from app.core.exceptions import GeminiServiceError, MissingAPIKeyError
from app.domain.models import RetrievedContext
from app.domain.schemas import SourceReference, StructuredAnswer
from app.services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)

_USER_PROMPT_TEMPLATE = PromptTemplate.from_template(
    """Context excerpts from the user's uploaded documents:

{context}

---

Conversation so far is provided as prior turns. Answer the following
question using only the context above.

Question: {question}"""
)


class ChatService:
    """Coordinates retrieval and generation to answer questions over PDFs with Gemini."""

    def __init__(
        self,
        retrieval_service: RetrievalService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._retrieval_service = retrieval_service or RetrievalService(settings=self._settings)
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            api_key = self._settings.gemini_api_key or self._settings.openai_api_key
            if not api_key:
                raise MissingAPIKeyError()
            self._client = genai.Client(
                api_key=api_key,
            )
        return self._client

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def retrieve_context(
        self,
        question: str,
        top_k: int | None = None,
        document_ids: list[str] | None = None,
    ) -> list[RetrievedContext]:
        return self._retrieval_service.retrieve(question, top_k=top_k, document_ids=document_ids)

    def _build_user_prompt(self, question: str, contexts: list[RetrievedContext]) -> str:
        context_block = self._retrieval_service.format_context(contexts)
        return _USER_PROMPT_TEMPLATE.format(context=context_block, question=question)

    def _build_contents(
        self,
        question: str,
        contexts: list[RetrievedContext],
        history: list[dict[str, str]] | None = None,
    ) -> list[types.Content]:
        """Convert prior turns and current prompt into Gemini Content objects."""
        contents: list[types.Content] = []
        for turn in history or []:
            role = "model" if turn.get("role") in ("assistant", "model") else "user"
            content_text = turn.get("content", "").strip()
            if content_text:
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=content_text)],
                    )
                )

        user_prompt = self._build_user_prompt(question, contexts)
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_prompt)],
            )
        )
        return contents

    @staticmethod
    def contexts_to_sources(contexts: list[RetrievedContext]) -> list[SourceReference]:
        return [
            SourceReference(
                document_id=c.chunk.document_id,
                document_name=c.chunk.document_name,
                page_number=c.chunk.page_number,
                snippet=(c.chunk.content[:280] + "...")
                if len(c.chunk.content) > 280
                else c.chunk.content,
                relevance_score=round(c.score, 4),
            )
            for c in contexts
        ]

    # ------------------------------------------------------------------
    # Streaming generation (Gemini generate_content_stream)
    # ------------------------------------------------------------------
    def stream_answer(
        self,
        question: str,
        contexts: list[RetrievedContext],
        history: list[dict[str, str]] | None = None,
    ) -> Iterator[str]:
        """Yield answer text incrementally using Gemini streaming."""
        contents = self._build_contents(question, contexts, history)
        config = types.GenerateContentConfig(
            system_instruction=DEFAULT_SYSTEM_PROMPT,
            max_output_tokens=self._settings.gemini_max_output_tokens,
        )

        try:
            response_stream = self.client.models.generate_content_stream(
                model=self._settings.gemini_chat_model,
                contents=contents,
                config=config,
            )
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except APIError as exc:
            logger.exception("Gemini streaming call failed")
            raise GeminiServiceError(f"Streaming generation failed: {exc}") from exc
        except Exception as exc:
            logger.exception("Unexpected error during Gemini streaming call")
            raise GeminiServiceError(f"Streaming generation failed: {exc}") from exc

    def generate_answer(
        self,
        question: str,
        contexts: list[RetrievedContext],
        history: list[dict[str, str]] | None = None,
    ) -> str:
        """Non-streaming variant used for tests / fallback clients."""
        return "".join(self.stream_answer(question, contexts, history))

    # ------------------------------------------------------------------
    # Structured output generation (Gemini native JSON schema enforcement)
    # ------------------------------------------------------------------
    def generate_structured_answer(
        self,
        question: str,
        contexts: list[RetrievedContext],
        history: list[dict[str, str]] | None = None,
    ) -> StructuredAnswer:
        """Call Gemini with Pydantic schema to enforce structured JSON output."""
        contents = self._build_contents(question, contexts, history)
        config = types.GenerateContentConfig(
            system_instruction=STRUCTURED_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=StructuredAnswer,
            max_output_tokens=self._settings.gemini_max_output_tokens,
        )

        try:
            response = self.client.models.generate_content(
                model=self._settings.gemini_chat_model,
                contents=contents,
                config=config,
            )
        except APIError as exc:
            logger.exception("Gemini structured call failed")
            raise GeminiServiceError(f"Structured generation failed: {exc}") from exc
        except Exception as exc:
            logger.exception("Unexpected error during Gemini structured call")
            raise GeminiServiceError(f"Structured generation failed: {exc}") from exc

        raw_text = (response.text or "").strip()
        if not raw_text:
            raise GeminiServiceError("The model did not return an answer.")

        # Clean potential markdown fencing if present
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        try:
            parsed = StructuredAnswer.model_validate_json(raw_text.strip())
        except Exception as parse_exc:
            logger.exception("Failed to validate structured JSON from Gemini: %s", raw_text)
            raise GeminiServiceError(
                f"Failed to parse structured answer: {parse_exc}"
            ) from parse_exc

        # Ensure citations reflect what was retrieved if the model omitted them
        if not parsed.sources:
            parsed.sources = self.contexts_to_sources(contexts)
        return parsed
