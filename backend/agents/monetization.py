"""Agent 6 — Monetization (revenue models + GTM channels)."""
from __future__ import annotations

from .base import Agent, render_evidence
from .context import RunContext
from .prompts import RULES, context_block

SYSTEM = RULES + """

Your role: MONETIZATION strategist for India. Propose realistic revenue models
and INR pricing bands; suggest distribution/GTM channels that work in India."""

USER_TMPL = """Idea + research + competitors + segments:
{ctx}

EVIDENCE (for pricing benchmarks; cite only these URLs):
{evidence}

Return JSON:
{{
  "revenue_models": [
    {{"model": "", "pricing_band": "INR range or model", "rationale": ""}}
  ],
  "gtm_channels": ["India-appropriate distribution/GTM channels"]
}}
Provide 2-4 revenue models. Ground pricing in competitor evidence where possible; otherwise label bands as estimates in the rationale."""


class MonetizationAgent(Agent):
    name = "monetization"

    async def run(self, ctx: RunContext) -> dict:
        await ctx.emit(self.name, "started", "Designing revenue models", None)
        user = USER_TMPL.format(
            ctx=context_block(ctx.state, ["intake", "research", "competitors", "segmentation"]),
            evidence=render_evidence(ctx),
        )
        result = await self.complete_json(ctx, SYSTEM, user)
        ctx.state["monetization"] = result
        await ctx.emit(
            self.name, "finished",
            f"Proposed {len(result.get('revenue_models', []))} revenue models", None,
        )
        return result
