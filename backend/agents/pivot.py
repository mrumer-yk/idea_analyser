"""Agent — Pivot Strategist.

Given the full analysis (fit score, red-team risks, competitor gaps, demand
signals), proposes 2-3 concrete pivots that would be more winnable in India.
Always offers options, but is honest when the original is already strong.
"""
from __future__ import annotations

from .base import Agent
from .context import RunContext
from .prompts import RULES, context_block

SYSTEM = RULES + """

Your role: PIVOT STRATEGIST. Propose 2-3 CONCRETE pivots that would make this
idea more winnable in India, grounded in the analysis (low-scoring fit factors,
red-team weaknesses, competitor whitespace, and demand signals). A pivot is a
specific change in direction (narrow the segment, change the wedge, reposition,
re-channel) — not vague advice. If the original is already strong, say so and
offer sharpening options instead."""

USER_TMPL = """Full analysis so far:
{ctx}

Return JSON:
{{
  "pivots": [
    {{"direction": "the concrete pivot in one line (e.g. 'Narrow to BFSI outbound calling only')",
      "rationale": "why pivot here, citing the relevant risk/gap/signal",
      "why_better": "why this is more winnable in India than the original"}}
  ]
}}
Give 2-3 pivots, most promising first."""


class PivotAgent(Agent):
    name = "pivots"

    async def run(self, ctx: RunContext) -> dict:
        await ctx.emit(self.name, "started", "Exploring pivot options", None)
        user = USER_TMPL.format(
            ctx=context_block(
                ctx.state,
                ["intake", "research", "demand", "competitors", "segmentation",
                 "sizing", "monetization", "fit", "redteam"],
            )
        )
        result = await self.complete_json(ctx, SYSTEM, user, max_tokens=2000)
        ctx.state["pivots"] = result
        await ctx.emit(
            self.name, "finished",
            f"Proposed {len(result.get('pivots', []))} pivots", None,
        )
        return result
