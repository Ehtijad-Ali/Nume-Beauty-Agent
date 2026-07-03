"""
AI agents — Phase 2 placeholder.

Will contain agent orchestration code: tool-use loops, planning, reflection,
and the agent registry. Each agent will be a class that exposes an `async def
run(input) -> output` coroutine and may compose multiple LLM calls, tool
calls and memory accesses.

Planned agents:
  * ContentGenerationAgent  — ad copy, emails, blog posts
  * CampaignOptimiserAgent  — bidding & creative recommendations
  * ReviewResponseAgent     — draft responses to customer reviews
  * CompetitorMonitorAgent  — summarise competitor changes

Phase 1.1 does NOT implement any agents.
"""


class BaseAgent:
    """Common interface that every agent will implement."""

    name: str = "base"
    description: str = ""

    async def run(self, input: str, **kwargs) -> str:
        """Run the agent on the given input and return its output."""
        raise NotImplementedError("Phase 2 — not yet implemented")
