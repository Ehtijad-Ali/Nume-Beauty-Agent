"""LLM provider clients — Phase 2.3.

A small, synchronous provider abstraction used by the RAG engine:

  * ``AnthropicProvider`` — Claude via the official ``anthropic`` SDK.
  * ``OpenAIProvider``    — GPT via the official ``openai`` SDK.
  * ``GeminiProvider``    — Gemini via the REST generateContent API (httpx).
  * ``MockLLMProvider``   — deterministic, dependency-free provider used by
    the test suite and for local development without API keys.

Every provider implements :meth:`BaseLLMProvider.complete` and returns an
:class:`LLMResponse` carrying the text plus token usage, so the engine can
record cost/latency for the admin panel.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.config.settings import get_settings
from app.core.exceptions import BadRequestError


@dataclass
class LLMResponse:
    """A completed LLM call with usage metadata."""

    text: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str | None = None


class BaseLLMProvider:
    """Common interface every provider implements."""

    name: str = "base"

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        """Generate a completion.

        ``messages`` is a list of ``{"role": "user"|"assistant", "content": str}``
        dicts, oldest first, ending with the current user message.
        """
        raise NotImplementedError


class AnthropicProvider(BaseLLMProvider):
    """Claude via the official Anthropic SDK (Messages API)."""

    name = "claude"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.claude_api_key:
            raise BadRequestError(
                "CLAUDE_API_KEY is not configured — set it in the backend .env "
                "or switch LLM_PROVIDER to 'openai'/'mock'.",
                error_code="llm_not_configured",
            )
        import anthropic

        self._client = anthropic.Anthropic(api_key=settings.claude_api_key)
        self.model = settings.claude_model
        self._default_max_tokens = settings.llm_max_tokens

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
        temperature: float | None = None,  # noqa: ARG002 — rejected by Opus 4.8
    ) -> LLMResponse:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self._default_max_tokens,
            system=system,
            messages=messages,
        )
        text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        return LLMResponse(
            text=text,
            provider=self.name,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            stop_reason=response.stop_reason,
        )


class OpenAIProvider(BaseLLMProvider):
    """GPT via the official OpenAI SDK (Chat Completions API)."""

    name = "openai"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise BadRequestError(
                "OPENAI_API_KEY is not configured — set it in the backend .env "
                "or switch LLM_PROVIDER to 'claude'/'mock'.",
                error_code="llm_not_configured",
            )
        from openai import OpenAI

        self._client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self._default_max_tokens = settings.llm_max_tokens
        self._default_temperature = settings.llm_temperature

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens or self._default_max_tokens,
            temperature=self._default_temperature if temperature is None else temperature,
            messages=[{"role": "system", "content": system}, *messages],
        )
        usage = response.usage
        return LLMResponse(
            text=response.choices[0].message.content or "",
            provider=self.name,
            model=response.model,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            stop_reason=response.choices[0].finish_reason,
        )


class GeminiProvider(BaseLLMProvider):
    """Gemini via the REST ``generateContent`` endpoint.

    Uses ``httpx`` (already a transitive dependency) instead of the Google
    SDK to keep the dependency tree small.
    """

    name = "gemini"

    _BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise BadRequestError(
                "GEMINI_API_KEY is not configured — set it in the backend .env "
                "or switch LLM_PROVIDER to 'claude'/'openai'/'mock'.",
                error_code="llm_not_configured",
            )
        import httpx

        self._client = httpx.Client(timeout=60.0)
        self._api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self._default_max_tokens = settings.llm_max_tokens
        self._default_temperature = settings.llm_temperature

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        contents = [
            {
                "role": "user" if m["role"] == "user" else "model",
                "parts": [{"text": m["content"]}],
            }
            for m in messages
        ]
        response = self._client.post(
            f"{self._BASE_URL}/{self.model}:generateContent",
            headers={"x-goog-api-key": self._api_key},
            json={
                "system_instruction": {"parts": [{"text": system}]},
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": max_tokens or self._default_max_tokens,
                    "temperature": (
                        self._default_temperature if temperature is None else temperature
                    ),
                    # Gemini 2.5 models spend the token budget on internal
                    # "thinking" by default; disable it so short answers
                    # don't come back empty.
                    "thinkingConfig": {"thinkingBudget": 0},
                },
            },
        )
        if response.status_code != 200:
            raise BadRequestError(
                f"Gemini API error {response.status_code}: {response.text[:300]}",
                error_code="llm_upstream_error",
            )
        data = response.json()
        candidate = (data.get("candidates") or [{}])[0]
        parts = candidate.get("content", {}).get("parts", [])
        usage = data.get("usageMetadata", {})
        return LLMResponse(
            text="".join(p.get("text", "") for p in parts),
            provider=self.name,
            model=data.get("modelVersion", self.model),
            input_tokens=usage.get("promptTokenCount", 0),
            output_tokens=usage.get("candidatesTokenCount", 0),
            stop_reason=candidate.get("finishReason"),
        )


class MockLLMProvider(BaseLLMProvider):
    """Deterministic offline provider for tests and keyless development.

    Produces an answer that references the injected context so grounding and
    citation plumbing can be asserted without a network call. Token counts
    are estimated at ~4 chars/token.
    """

    name = "mock"
    model = "mock-llm"

    def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,  # noqa: ARG002
        temperature: float | None = None,  # noqa: ARG002
    ) -> LLMResponse:
        question = messages[-1]["content"] if messages else ""
        history_turns = max(0, len(messages) - 1)
        cited = "[1]" if "[1]" in system else ""
        text = (
            f"Mock answer to: {question.strip()[:200]} {cited}\n"
            f"(grounded on provided context; history_turns={history_turns})"
        ).strip()
        input_chars = len(system) + sum(len(m["content"]) for m in messages)
        return LLMResponse(
            text=text,
            provider=self.name,
            model=self.model,
            input_tokens=max(1, input_chars // 4),
            output_tokens=max(1, len(text) // 4),
            stop_reason="end_turn",
        )


@lru_cache(maxsize=1)
def get_llm_provider() -> BaseLLMProvider:
    """Return the process-wide LLM provider configured in settings."""
    provider = get_settings().llm_provider
    if provider == "claude":
        return AnthropicProvider()
    if provider == "openai":
        return OpenAIProvider()
    if provider == "gemini":
        return GeminiProvider()
    return MockLLMProvider()


def reset_llm_provider_cache() -> None:
    """Drop the cached provider (test isolation helper)."""
    get_llm_provider.cache_clear()
