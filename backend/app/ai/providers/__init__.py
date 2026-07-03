"""
LLM provider clients — Phase 2 placeholder.

Each provider will be implemented as a class with a common interface, e.g.::

    class LLMProvider(Protocol):
        async def complete(self, prompt: str, *, model: str, **kwargs) -> str: ...

Planned providers:
  * OpenAIProvider   (GPT-4o, GPT-4 Turbo)
  * AnthropicProvider (Claude 3.5 Sonnet, Haiku)
  * GeminiProvider   (Gemini 1.5 Pro, Flash)
  * CohereProvider   (Command R+)
  * MistralProvider  (Mistral Large, Nemo)

API keys are already stored in app settings (see app.config.settings) and in
the settings table — wiring will happen here in Phase 2.
"""


class BaseLLMProvider:
    """Common interface that every provider client will implement."""

    name: str = "base"

    async def complete(self, prompt: str, *, model: str | None = None, **kwargs) -> str:
        """Generate a completion for the given prompt."""
        raise NotImplementedError("Phase 2 — not yet implemented")

    async def stream(self, prompt: str, *, model: str | None = None, **kwargs):
        """Stream a completion token-by-token."""
        raise NotImplementedError("Phase 2 — not yet implemented")
        # pragma: no cover
        yield ""  # type: ignore[unreachable]
