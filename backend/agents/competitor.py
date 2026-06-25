"""Agent 3 — Competitor Analyst."""
from __future__ import annotations

from .base import Agent, render_evidence
from .context import RunContext
from .prompts import RULES, context_block

SYSTEM = RULES + """

Your role: COMPETITOR ANALYST for the Indian market."""

USER_TMPL = """Idea + research context:
{ctx}

EVIDENCE (cite only these URLs):
{evidence}

Identify direct and indirect competitors operating in or serving India.
Return JSON:
{{
  "competitors": [
    {{"name": "", "type": "direct|indirect", "positioning": "",
      "pricing": "INR pricing if known, else ''", "url": "EVIDENCE url or ''"}}
  ],
  "gaps": ["whitespace / unmet needs vs. these competitors"]
}}
Only include competitors you can ground in the evidence or that are well-known in India; do not invent."""


class CompetitorAgent(Agent):
    name = "competitor"

    async def run(self, ctx: RunContext) -> dict:
        await ctx.emit(self.name, "started", "Mapping competitors", None)
        user = USER_TMPL.format(
            ctx=context_block(ctx.state, ["intake", "research"]),
            evidence=render_evidence(ctx),
        )
        result = await self.complete_json(ctx, SYSTEM, user)
        ctx.state["competitors"] = result
        await ctx.emit(
            self.name, "finished",
            f"Found {len(result.get('competitors', []))} competitors", None,
        )
        return result
