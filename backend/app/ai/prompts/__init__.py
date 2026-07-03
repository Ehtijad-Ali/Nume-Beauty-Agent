"""
Prompt templates — Phase 2 placeholder.

Will host a registry of versioned, parameterised prompt templates for content
generation, summarisation, classification, etc. Templates will be loaded from
the database (or YAML files) and rendered with Jinja2.

Phase 1.1 does NOT implement any prompt templates.
"""

from __future__ import annotations


class PromptTemplate:
    """A parameterised prompt template (Phase 2 placeholder)."""

    def __init__(self, name: str, template: str, *, version: str = "1.0") -> None:
        self.name = name
        self.template = template
        self.version = version

    def render(self, **kwargs) -> str:
        """Render the template with the given variables."""
        raise NotImplementedError("Phase 2 — not yet implemented")


# Registry will live here in Phase 2:
# PROMPT_REGISTRY: dict[str, PromptTemplate] = {}
