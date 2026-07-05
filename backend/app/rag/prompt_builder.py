"""Prompt builder — Phase 2.3.

Builds the system prompt (grounding rules + brand context + retrieved
knowledge) and the message list (conversation memory + current question)
sent to the LLM.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.brand_guideline import BrandGuideline

SYSTEM_PROMPT = """\
You are the NUMÉ AI Marketing Assistant, a retrieval-augmented assistant for
the NUMÉ beauty brand. You answer questions using the brand's uploaded
knowledge base.

Rules:
1. Always base your answer on the retrieved knowledge below.
2. {grounding_rule}
3. When sources conflict, prioritise in this order: Brand Guidelines,
   Brand Voice, Product Catalogue, Customer Personas, then everything else.
4. Cite the context passages you used with bracketed numbers, e.g. [1] or
   [2][3], matching the numbering of the retrieved context.
5. Keep answers concise, accurate and in the brand's voice.
"""

GROUNDED_ONLY = (
    "Never answer from outside the retrieved knowledge. If the retrieved "
    "context does not contain the answer, say you don't have that information "
    "in the knowledge base — do not guess or use general knowledge."
)
GENERAL_ALLOWED = (
    "Prefer the retrieved knowledge. If it does not contain the answer, you "
    "may carefully use general knowledge, but say explicitly that the answer "
    "is not from the uploaded knowledge base."
)


def build_brand_context(db: Session, *, max_items: int = 8, max_chars: int = 2000) -> str:
    """Summarise active brand guidelines for prompt injection."""
    guidelines = (
        db.query(BrandGuideline)
        .filter(BrandGuideline.is_active.is_(True))
        .order_by(BrandGuideline.created_at)
        .limit(max_items)
        .all()
    )
    lines: list[str] = []
    used = 0
    for g in guidelines:
        content = (g.content or "").strip()
        line = f"- {g.name} ({g.guideline_type}): {content}" if content else f"- {g.name} ({g.guideline_type})"
        if used + len(line) > max_chars:
            break
        lines.append(line)
        used += len(line)
    return "\n".join(lines)


def build_system_prompt(
    *,
    context: str,
    brand_context: str,
    allow_general_knowledge: bool,
) -> str:
    """Compose the final system prompt."""
    prompt = SYSTEM_PROMPT.format(
        grounding_rule=GENERAL_ALLOWED if allow_general_knowledge else GROUNDED_ONLY
    )
    if brand_context:
        prompt += f"\nBrand context (always respect this):\n{brand_context}\n"
    if context:
        prompt += f"\nRetrieved knowledge:\n{context}\n"
    else:
        prompt += "\nRetrieved knowledge: (nothing relevant was found)\n"
    return prompt


def build_messages(
    history: list[dict[str, str]],
    question: str,
) -> list[dict[str, str]]:
    """Conversation memory + the current user question, oldest first."""
    messages: list[dict[str, str]] = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("content") and m.get("role") in ("user", "assistant")
    ]
    messages.append({"role": "user", "content": question})
    return messages


def prompt_debug_payload(system: str, messages: list[dict[str, str]]) -> dict[str, Any]:
    """The exact prompt sent to the LLM, for the admin prompt debugger."""
    return {"system": system, "messages": messages}
