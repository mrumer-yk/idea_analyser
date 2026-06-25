"""Agent 4 — Segmentation / Persona."""
from __future__ import annotations

from .base import Agent
from .context import RunContext
from .prompts import RULES, context_block

SYSTEM = RULES + """

Your role: CUSTOMER SEGMENTATION analyst for India."""

USER_TMPL = """Idea + research context:
{ctx}

Define the target customer segments and personas for the Indian market.
Return JSON:
{{
  "segments": [
    {{"segment": "", "persona": "short persona name + description",
      "pains": [""], "jtbd": ["jobs to be done"]}}
  ]
}}
Provide 2-4 segments grounded in the idea and Indian context."""


class SegmentationAgent(Agent):
    name = "segmentation"

    async def run(self, ctx: RunContext) -> dict:
        await ctx.emit(self.name, "started", "Defining segments & personas", None)
        user = USER_TMPL.format(ctx=context_block(ctx.state, ["intake", "research"]))
        result = await self.complete_json(ctx, SYSTEM, user)
        ctx.state["segmentation"] = result
        await ctx.emit(
            self.name, "finished",
            f"Defined {len(result.get('segments', []))} segments", None,
        )
        return result
